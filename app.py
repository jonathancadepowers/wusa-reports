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
        "📋 Team vs Date Matrix",
        "✉️ Request Schedule Change",
        "📋 View Requests"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(f"**Total Games:** {len(df)}")

# Main content
if page == "📅 Full Schedule":
    st.title("📅 Full Schedule")
    
    # Filters - now in 2 rows
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_divisions = st.multiselect(
            "Division", 
            sorted(df['Division'].unique()), 
            default=sorted(df['Division'].unique())
        )
    with col2:
        selected_weeks = st.multiselect(
            "Week", 
            sorted(df['Week'].unique()), 
            default=sorted(df['Week'].unique())
        )
    with col3:
        selected_fields = st.multiselect("Field", sorted(df['Field'].unique()))
    
    # Second row for team filter
    col4, col5, col6 = st.columns(3)
    with col4:
        # Get all unique teams (both home and away), filtering out NaN values
        home_teams = df['Home'].dropna().unique()
        away_teams = df['Away'].dropna().unique()
        all_teams = sorted(set(list(home_teams) + list(away_teams)))
        
        selected_teams = st.multiselect("Team (Home or Away)", all_teams)
    
    # Filter data
    filtered_df = df[
        df['Division'].isin(selected_divisions) & 
        df['Week'].isin(selected_weeks)
    ]
    
    if selected_fields:
        filtered_df = filtered_df[filtered_df['Field'].isin(selected_fields)]
    
    if selected_teams:
        # Filter to games where the selected team is either home or away
        filtered_df = filtered_df[
            filtered_df['Home'].isin(selected_teams) | 
            filtered_df['Away'].isin(selected_teams)
        ]
    
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
    selected_week = st.selectbox("Select Week", sorted(df['Week'].unique()))
    
    # Filter by week
    week_df = df[df['Week'] == selected_week]
    
    # Create pivot table
    pivot = week_df.pivot_table(
        index='Time',
        columns='Field',
        values='Division',
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
    
    # Get all unique teams (both home and away), filtering out NaN values
    home_teams = df['Home'].dropna().unique()
    away_teams = df['Away'].dropna().unique()
    all_teams = sorted(set(list(home_teams) + list(away_teams)))
    
    # Team selector
    selected_team = st.selectbox("Select Team", all_teams)
    
    # Filter games for this team
    team_games = df[
        (df['Home'] == selected_team) | 
        (df['Away'] == selected_team)
    ].copy()
    
    # Add Home/Away indicator
    team_games['Home/Away'] = team_games.apply(
        lambda row: 'Home' if row['Home'] == selected_team else 'Away',
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
        team_games[['Week', 'Game Date', 'Time', 'Field', 'Home', 'Away', 'Home/Away']],
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
    div_counts = df.groupby('Division').size().sort_values(ascending=False)
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
    week_div = df.groupby(['Week', 'Division']).size().reset_index(name='Games')
    pivot_week = week_div.pivot(index='Week', columns='Division', values='Games').fillna(0)
    st.line_chart(pivot_week)

elif page == "📋 Team vs Date Matrix":
    st.title("📋 Team vs Date Matrix")
    
    st.markdown("""
    This view shows how many games each team plays on each date.
    Similar to the matrix in your Google Sheet.
    """)
    
    # Division filter
    selected_division = st.selectbox(
        "Select Division", 
        sorted(df['Division'].unique())
    )
    
    # Filter by division
    division_df = df[df['Division'] == selected_division].copy()
    
    # Get all teams for this division
    home_teams = division_df['Home'].dropna().unique()
    away_teams = division_df['Away'].dropna().unique()
    all_teams = sorted(set(list(home_teams) + list(away_teams)))
    
    # Create a list to hold team game counts per date
    matrix_data = []
    
    for team in all_teams:
        team_row = {'Team': team}
        
        # For each unique date, count games
        for date in sorted(division_df['Game Date'].unique()):
            games_on_date = division_df[
                ((division_df['Home'] == team) | (division_df['Away'] == team)) &
                (division_df['Game Date'] == date)
            ]
            count = len(games_on_date)
            team_row[date] = count if count > 0 else ''
        
        # Add total games column
        team_total = len(division_df[
            (division_df['Home'] == team) | (division_df['Away'] == team)
        ])
        team_row['Total Games'] = team_total
        
        matrix_data.append(team_row)
    
    # Convert to DataFrame
    matrix_df = pd.DataFrame(matrix_data)
    
    # Set Team as index
    matrix_df = matrix_df.set_index('Team')
    
    # Display the matrix
    st.dataframe(
        matrix_df,
        use_container_width=True
    )
    
    # Download button
    csv = matrix_df.to_csv()
    st.download_button(
        "📥 Download as CSV",
        csv,
        f"team_date_matrix_{selected_division}.csv",
        "text/csv"
    )

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
            selected_division = st.selectbox("Division", sorted(df['Division'].unique()))
        with col2:
            # Filter games by selected division
            division_games = df[df['Division'] == selected_division]
            game_options = [
                f"{row['Game Date']} - {row['Time']} - {row['Home']} vs {row['Away']}"
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