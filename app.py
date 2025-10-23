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
    ["📅 Full Schedule", "🏟️ Field Pivot", "👥 Team Schedules", "📊 Division Stats"]
)

st.sidebar.markdown("---")
st.sidebar.info(f"**Total Games:** {len(df)}")

# Main content
if page == "📅 Full Schedule":
    st.title("📅 Full Schedule")
    
    # Filters
    col1, col2 = st.columns(2)
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
    
    col3, col4 = st.columns(2)
    with col3:
        selected_fields = st.multiselect("Field", sorted(df['Field'].unique()))
    with col4:
        # Get all teams - filter out any None/NaN values
        home_teams = set(df['Home'].dropna().unique())
        away_teams = set(df['Away'].dropna().unique())
        all_teams = sorted(home_teams | away_teams)
        selected_teams = st.multiselect("Team", all_teams)
    
    # Filter data
    filtered_df = df[
        df['Division'].isin(selected_divisions) & 
        df['Week'].isin(selected_weeks)
    ]
    if selected_fields:
        filtered_df = filtered_df[filtered_df['Field'].isin(selected_fields)]
    if selected_teams:
        # Filter to games where selected teams are either home or away
        filtered_df = filtered_df[
            filtered_df['Home'].isin(selected_teams) | 
            filtered_df['Away'].isin(selected_teams)
        ]
    
    # Display
    st.dataframe(
        filtered_df[['Week', 'Game Date', 'Time', 'Field', 'Division', 'Home', 'Away']],
        use_container_width=True,
        height=600
    )
    
    # Download button
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        "📥 Download Filtered Schedule (CSV)",
        csv,
        "filtered_schedule.csv",
        "text/csv"
    )

elif page == "🏟️ Field Pivot":
    st.title("🏟️ Field Utilization Report")
    
    # Create pivot table
    pivot = df.pivot_table(
        index=['Game Date', 'Time'],
        columns='Field',
        values='Week',
        aggfunc='count',
        fill_value=0
    )
    
    # Add grand total
    pivot['Grand Total'] = pivot.sum(axis=1)
    
    # Display
    st.dataframe(pivot, use_container_width=True, height=600)
    
    # Summary stats
    st.markdown("### Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Time Slots", len(pivot))
    with col2:
        st.metric("Busiest Slot", f"{int(pivot['Grand Total'].max())} games")
    with col3:
        st.metric("Avg Games/Slot", f"{pivot['Grand Total'].mean():.1f}")
    with col4:
        st.metric("Total Fields", len(pivot.columns) - 1)
    
    # Chart
    st.markdown("### Games Per Field")
    field_counts = df.groupby('Field').size().sort_values(ascending=False)
    st.bar_chart(field_counts)

elif page == "👥 Team Schedules":
    st.title("👥 Team Schedules")
    
    # Get all teams - filter out any None/NaN values
    home_teams = set(df['Home'].dropna().unique())
    away_teams = set(df['Away'].dropna().unique())
    all_teams = sorted(home_teams | away_teams)
    
    # Team selector
    selected_team = st.selectbox("Select Team", all_teams)
    
    if selected_team:
        # Get team's games
        team_games = df[
            (df['Home'] == selected_team) | (df['Away'] == selected_team)
        ].copy()
        
        # Add opponent column
        team_games['Opponent'] = team_games.apply(
            lambda row: row['Away'] if row['Home'] == selected_team else row['Home'],
            axis=1
        )
        
        # Add home/away indicator
        team_games['Home/Away'] = team_games.apply(
            lambda row: 'Home' if row['Home'] == selected_team else 'Away',
            axis=1
        )
        
        # Display
        st.markdown(f"### {selected_team} - {len(team_games)} Games")
        
        st.dataframe(
            team_games[['Week', 'Game Date', 'Time', 'Field', 'Opponent', 'Home/Away']],
            use_container_width=True
        )
        
        # Stats
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Games", len(team_games))
        with col2:
            home_games = len(team_games[team_games['Home/Away'] == 'Home'])
            st.metric("Home Games", home_games)
        with col3:
            away_games = len(team_games[team_games['Home/Away'] == 'Away'])
            st.metric("Away Games", away_games)
        with col4:
            division = team_games['Division'].iloc[0]
            st.metric("Division", division)
        
        # Download team schedule
        csv = team_games[['Game Date', 'Time', 'Field', 'Opponent', 'Home/Away']].to_csv(index=False)
        st.download_button(
            f"📥 Download {selected_team} Schedule",
            csv,
            f"{selected_team}_schedule.csv",
            "text/csv"
        )

elif page == "📊 Division Stats":
    st.title("📊 Division Statistics")
    
    # Games per division
    st.markdown("### Games Per Division")
    div_counts = df.groupby('Division').size().sort_values(ascending=False)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.bar_chart(div_counts)
    
    with col2:
        st.dataframe(
            pd.DataFrame({
                'Division': div_counts.index,
                'Total Games': div_counts.values
            }),
            use_container_width=True
        )
    
    # Games per week by division
    st.markdown("### Games Per Week by Division")
    week_div = df.groupby(['Week', 'Division']).size().reset_index(name='Games')
    pivot_week = week_div.pivot(index='Week', columns='Division', values='Games').fillna(0)
    st.line_chart(pivot_week)
    
    # Team counts per division
    st.markdown("### Teams Per Division")
    team_counts = []
    for division in sorted(df['Division'].unique()):
        div_games = df[df['Division'] == division]
        # Filter out None/NaN values when getting teams
        home_teams = set(div_games['Home'].dropna().unique())
        away_teams = set(div_games['Away'].dropna().unique())
        teams = home_teams | away_teams
        team_counts.append({'Division': division, 'Teams': len(teams)})
    
    st.dataframe(pd.DataFrame(team_counts), use_container_width=True)