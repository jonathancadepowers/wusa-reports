# app.py
import streamlit as st
import pandas as pd
import sqlite3

# Page config
st.set_page_config(
    page_title="WUSA Schedule Reports",
    page_icon="⚾",
    layout="wide"
)

# Load data (cached so it's fast)
@st.cache_data
def load_games():
    conn = sqlite3.connect('wusa_schedule.db')
    df = pd.read_sql("SELECT * FROM games", conn)
    conn.close()
    return df

df = load_games()

# Sidebar
st.sidebar.title("⚾ WUSA Schedule")
st.sidebar.markdown("**Fall 2025**")
st.sidebar.markdown("---")

# Page selection
page = st.sidebar.radio(
    "Select Report:",
    [
        "📅 Full Schedule", 
        "🏟️ Field Pivot", 
        "👥 Team Schedules", 
        "📊 Division Stats",
        "✉️ Request Schedule Change",
        "📋 View Requests"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(f"**Total Games:** {len(df)}")

# Main content
if page == "📅 Full Schedule":
    st.title("📅 Full Schedule")
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_divisions = st.multiselect(
            "Division", 
            sorted(df['DIVISION'].unique()), 
            default=sorted(df['DIVISION'].unique())
        )
    with col2:
        selected_weeks = st.multiselect(
            "Week", 
            sorted(df['WEEK'].unique()), 
            default=sorted(df['WEEK'].unique())
        )
    with col3:
        selected_fields = st.multiselect("Field", sorted(df['FIELD'].unique()))
    
    # Filter data
    filtered_df = df[
        df['DIVISION'].isin(selected_divisions) & 
        df['WEEK'].isin(selected_weeks)
    ]
    if selected_fields:
        filtered_df = filtered_df[filtered_df['FIELD'].isin(selected_fields)]
    
    # Display
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        "📥 Download as CSV",
        csv,
        "wusa_schedule.csv",
        "text/csv"
    )

elif page == "🏟️ Field Pivot":
    st.title("🏟️ Field Pivot Report")
    
    # Week filter
    selected_week = st.selectbox("Select Week", sorted(df['WEEK'].unique()))
    
    # Filter by week
    week_df = df[df['WEEK'] == selected_week]
    
    # Create pivot table
    pivot = week_df.pivot_table(
        index='TIME',
        columns='FIELD',
        values='DIVISION',
        aggfunc='first',
        fill_value=''
    )
    
    st.dataframe(
        pivot,
        use_container_width=True
    )
    
    # Download button
    csv = pivot.to_csv()
    st.download_button(
        "📥 Download as CSV",
        csv,
        f"field_pivot_week_{selected_week}.csv",
        "text/csv"
    )

elif page == "👥 Team Schedules":
    st.title("👥 Team Schedules")
    
    # Get all unique teams (both home and away)
    home_teams = df['HOME TEAM'].unique()
    away_teams = df['AWAY TEAM'].unique()
    all_teams = sorted(set(list(home_teams) + list(away_teams)))
    
    # Team selector
    selected_team = st.selectbox("Select Team", all_teams)
    
    # Filter games for this team
    team_games = df[
        (df['HOME TEAM'] == selected_team) | 
        (df['AWAY TEAM'] == selected_team)
    ].copy()
    
    # Add Home/Away indicator
    team_games['Home/Away'] = team_games.apply(
        lambda row: 'Home' if row['HOME TEAM'] == selected_team else 'Away',
        axis=1
    )
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Games", len(team_games))
    with col2:
        home_games = len(team_games[team_games['Home/Away'] == 'Home'])
        st.metric("Home Games", home_games)
    with col3:
        away_games = len(team_games[team_games['Home/Away'] == 'Away'])
        st.metric("Away Games", away_games)
    
    # Display schedule
    st.dataframe(
        team_games[['WEEK', 'DATE', 'TIME', 'FIELD', 'HOME TEAM', 'AWAY TEAM', 'Home/Away']],
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = team_games.to_csv(index=False)
    st.download_button(
        "📥 Download as CSV",
        csv,
        f"{selected_team}_schedule.csv",
        "text/csv"
    )

elif page == "📊 Division Stats":
    st.title("📊 Division Statistics")
    
    # Games per division
    st.markdown("### Games Per Division")
    div_counts = df.groupby('DIVISION').size().sort_values(ascending=False)
    st.bar_chart(div_counts)
    
    # Show table
    st.dataframe(
        pd.DataFrame({
            'Division': div_counts.index,
            'Total Games': div_counts.values
        }),
        use_container_width=True,
        hide_index=True
    )
    
    # Games per week by division
    st.markdown("### Games Per Week by Division")
    week_div = df.groupby(['WEEK', 'DIVISION']).size().reset_index(name='Games')
    pivot_week = week_div.pivot(index='WEEK', columns='DIVISION', values='Games').fillna(0)
    st.line_chart(pivot_week)

elif page == "✉️ Request Schedule Change":
    st.title("✉️ Request Schedule Change")
    
    st.markdown("""
    Use this form to request changes to the schedule. Your request will be 
    logged and reviewed by the scheduling team.
    """)
    
    with st.form("schedule_request_form"):
        # Email address (required)
        email = st.text_input(
            "Your Email Address *",
            placeholder="your.email@example.com",
            help="We'll use this to follow up on your request"
        )
        
        # Game selection
        col1, col2 = st.columns(2)
        with col1:
            selected_division = st.selectbox("Division", sorted(df['DIVISION'].unique()))
        with col2:
            # Filter games by selected division
            division_games = df[df['DIVISION'] == selected_division]
            game_options = [
                f"{row['DATE']} - {row['TIME']} - {row['HOME TEAM']} vs {row['AWAY TEAM']}"
                for _, row in division_games.iterrows()
            ]
            selected_game = st.selectbox("Select Game", game_options)
        
        # Request type
        request_type = st.selectbox(
            "Type of Request",
            ["Reschedule Game", "Change Field", "Change Time", "Other"]
        )
        
        # Reason (required)
        reason = st.text_area(
            "Reason for Request *",
            placeholder="Please explain why you need this change...",
            height=150,
            help="Be as specific as possible to help us process your request"
        )
        
        # Submit button
        submitted = st.form_submit_button("Submit Request", type="primary")
        
        if submitted:
            # Validation
            if not email or not email.strip():
                st.error("❌ Email address is required")
            elif "@" not in email:
                st.error("❌ Please enter a valid email address")
            elif not reason or not reason.strip():
                st.error("❌ Please provide a reason for your request")
            else:
                # Save to database
                conn = sqlite3.connect('wusa_schedule.db')
                cursor = conn.cursor()
                
                # Create requests table if it doesn't exist
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS schedule_requests (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT NOT NULL,
                        division TEXT,
                        game_details TEXT,
                        request_type TEXT,
                        reason TEXT NOT NULL,
                        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        status TEXT DEFAULT 'Pending'
                    )
                ''')
                
                # Insert the request
                cursor.execute('''
                    INSERT INTO schedule_requests 
                    (email, division, game_details, request_type, reason)
                    VALUES (?, ?, ?, ?, ?)
                ''', (email, selected_division, selected_game, request_type, reason))
                
                conn.commit()
                request_id = cursor.lastrowid
                conn.close()
                
                st.success(f"✅ Request #{request_id} submitted successfully!")
                st.info(f"📧 Confirmation will be sent to {email}")
                
                # Show what was submitted
                with st.expander("View Submitted Request"):
                    st.write(f"**Request ID:** {request_id}")
                    st.write(f"**Email:** {email}")
                    st.write(f"**Division:** {selected_division}")
                    st.write(f"**Game:** {selected_game}")
                    st.write(f"**Type:** {request_type}")
                    st.write(f"**Reason:** {reason}")

elif page == "📋 View Requests":
    st.title("📋 Schedule Change Requests")
    
    # Load requests from database
    conn = sqlite3.connect('wusa_schedule.db')
    
    # Check if table exists
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='schedule_requests'
    """)
    table_exists = cursor.fetchone() is not None
    
    if not table_exists:
        st.info("No requests submitted yet. The requests table will be created when the first request is submitted.")
        conn.close()
    else:
        requests_df = pd.read_sql("""
            SELECT 
                id,
                email,
                division,
                game_details,
                request_type,
                reason,
                submitted_at,
                status
            FROM schedule_requests
            ORDER BY submitted_at DESC
        """, conn)
        conn.close()
        
        if len(requests_df) == 0:
            st.info("No requests submitted yet")
        else:
            # Filter by status
            status_filter = st.multiselect(
                "Filter by Status",
                ["Pending", "Approved", "Denied"],
                default=["Pending"]
            )
            
            filtered_requests = requests_df[requests_df['status'].isin(status_filter)]
            
            # Display count
            st.metric("Total Requests", len(filtered_requests))
            
            # Display requests
            st.dataframe(
                filtered_requests,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": "ID",
                    "email": "Email",
                    "division": "Division",
                    "game_details": "Game",
                    "request_type": "Type",
                    "reason": st.column_config.TextColumn("Reason", width="large"),
                    "submitted_at": st.column_config.DatetimeColumn(
                        "Submitted", 
                        format="MMM D, YYYY h:mm A"
                    ),
                    "status": "Status"
                }
            )
            
            # Download button
            csv = filtered_requests.to_csv(index=False)
            st.download_button(
                "📥 Download as CSV",
                csv,
                "schedule_requests.csv",
                "text/csv"
            )