# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

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
    # Convert Game Date to datetime for filtering
    df['Game Date Parsed'] = pd.to_datetime(df['Game Date'])
    return df

# Helper function to sort divisions numerically (7U, 8U, 9U, 10U, 12U, 14U)
def sort_divisions(divisions):
    def get_numeric_value(div):
        try:
            # Extract numeric part from division (e.g., "10U" -> 10)
            return int(''.join(filter(str.isdigit, str(div))))
        except:
            return 999  # Put non-numeric divisions at the end
    return sorted(divisions, key=get_numeric_value)

df = load_games()

# Sidebar
st.sidebar.title("⚾ WUSA Schedule")
st.sidebar.markdown("**Fall 2025**")

# Single radio group with all pages
page = st.sidebar.radio(
    "",
    [
        "📅 Full Schedule", 
        "🏟️ Field Pivot", 
        "👥 Team Schedules",
        "📋 Team vs Date Matrix",
        "📊 Division Summary",
        "📅 Teams by Day",
        "✉️ Request Change",
        "✏️ Edit Game*",
        "📋 View Requests*"
    ]
)

st.sidebar.markdown("*Admin Pages")

st.sidebar.info(f"**Total Games:** {len(df)}")

# Main content
if page == "📅 Full Schedule":
    st.title("📅 Full Schedule")
    
    # Filters - now in 3 rows
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_divisions = st.multiselect(
            "Division", 
            sort_divisions(df['Division'].unique()), 
            default=sort_divisions(df['Division'].unique())
        )
    with col2:
        selected_weeks = st.multiselect(
            "Week", 
            sorted(df['Week'].unique()), 
            default=sorted(df['Week'].unique())
        )
    with col3:
        selected_fields = st.multiselect("Field", sorted(df['Field'].unique()))
    
    # Second row for team filter and date range
    col4, col5, col6 = st.columns(3)
    with col4:
        # Get all unique teams (both home and away), filtering out NaN values
        home_teams = df['Home'].dropna().unique()
        away_teams = df['Away'].dropna().unique()
        all_teams = sorted(set(list(home_teams) + list(away_teams)))
        
        selected_teams = st.multiselect("Team (Home or Away)", all_teams)
    with col5:
        # Get min and max dates from the schedule
        min_date = df['Game Date Parsed'].min().date()
        max_date = df['Game Date Parsed'].max().date()
        
        start_date = st.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
    with col6:
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
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
    
    # Apply date range filter
    filtered_df = filtered_df[
        (filtered_df['Game Date Parsed'].dt.date >= start_date) &
        (filtered_df['Game Date Parsed'].dt.date <= end_date)
    ]
    
    # Drop the parsed date column before displaying
    display_df = filtered_df.drop(columns=['Game Date Parsed'])
    
    # Display with editable Comment column
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        hide_index=True,
        disabled=[col for col in display_df.columns if col != 'Comment'],  # Only Comment is editable
        key="schedule_editor"
    )
    
    st.markdown("💡 **Tip:** You can edit the Comment column directly - changes are saved automatically! Only those with access to this page can view these comments.")
    
    # Check if any comments were edited
    if not edited_df.equals(display_df):
        # Find rows where Comment changed
        changed_rows = edited_df[edited_df['Comment'] != display_df['Comment']]
        
        if len(changed_rows) > 0:
            # Update database for each changed row
            conn = sqlite3.connect('wusa_schedule.db')
            cursor = conn.cursor()
            
            for idx, row in changed_rows.iterrows():
                cursor.execute(
                    'UPDATE games SET "Comment" = ? WHERE "Game #" = ?',
                    (row['Comment'], row['Game #'])
                )
            
            conn.commit()
            conn.close()
            
            # Clear cache to reload data
            st.cache_data.clear()
            
            # Show success message
            st.success(f"✅ Updated {len(changed_rows)} comment(s) automatically!")
            
            # Small delay to show message, then rerun
            import time
            time.sleep(1)
            st.rerun()
    
    # Download button
    csv = edited_df.to_csv(index=False)
    st.download_button(
        "📥 Download as CSV",
        csv,
        "wusa_schedule.csv",
        "text/csv"
    )

elif page == "🏟️ Field Pivot":
    st.title("🏟️ Field Pivot Report")
    
    # Filters in columns
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_week = st.selectbox("Week", sorted(df['Week'].unique()))
    with col2:
        # Get min and max dates from the schedule
        min_date = df['Game Date Parsed'].min().date()
        max_date = df['Game Date Parsed'].max().date()
        
        start_date = st.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key="field_pivot_start_date"
        )
    with col3:
        end_date = st.date_input(
            "End Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="field_pivot_end_date"
        )
    
    # Filter by week and date range
    week_df = df[
        (df['Week'] == selected_week) &
        (df['Game Date Parsed'].dt.date >= start_date) &
        (df['Game Date Parsed'].dt.date <= end_date)
    ]
    
    # Create a dictionary to store game details for tooltips
    game_details = {}
    for _, row in week_df.iterrows():
        key = (row['Time'], row['Field'])
        if key not in game_details:
            game_details[key] = []
        game_info = f"{row['Home']} vs {row['Away']}"
        game_details[key].append(game_info)
    
    # Create pivot table
    pivot = week_df.pivot_table(
        index='Time',
        columns='Field',
        values='Division',
        aggfunc='first',
        fill_value=''
    )
    
    # Generate HTML table with hover tooltips
    html = """
    <style>
        .pivot-table {
            border-collapse: collapse;
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
        }
        .pivot-table th, .pivot-table td {
            border: 1px solid #ddd;
            padding: 12px 16px;
            text-align: center;
        }
        .pivot-table th {
            background-color: #f0f2f6;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .pivot-table tr:hover {
            background-color: #f8f9fa;
        }
        .tooltip-cell {
            position: relative;
            cursor: help;
            color: #0066cc;
            font-weight: 500;
        }
        .tooltip-cell:hover {
            background-color: #e8f4f8;
        }
        .tooltip-cell .tooltiptext {
            visibility: hidden;
            width: 300px;
            background-color: #333;
            color: #fff;
            text-align: left;
            border-radius: 6px;
            padding: 12px;
            position: absolute;
            z-index: 1000;
            bottom: 125%;
            left: 50%;
            margin-left: -150px;
            opacity: 0;
            transition: opacity 0.3s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            font-size: 13px;
            line-height: 1.6;
        }
        .tooltip-cell .tooltiptext::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #333 transparent transparent transparent;
        }
        .tooltip-cell:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
        .game-item {
            padding: 4px 0;
            border-bottom: 1px solid #555;
        }
        .game-item:last-child {
            border-bottom: none;
        }
    </style>
    <table class="pivot-table">
        <thead>
            <tr>
                <th>Time</th>
    """
    
    # Add column headers (fields)
    for field in pivot.columns:
        html += f"<th>{field}</th>"
    html += "</tr></thead><tbody>"
    
    # Add data rows
    for time in pivot.index:
        html += f"<tr><th>{time}</th>"
        for field in pivot.columns:
            value = pivot.loc[time, field]
            key = (time, field)
            
            if value and key in game_details:
                # Create tooltip with game details
                tooltip_content = "<br>".join([f'<div class="game-item">{game}</div>' for game in game_details[key]])
                html += f'''<td class="tooltip-cell">
                    {value}
                    <span class="tooltiptext">{tooltip_content}</span>
                </td>'''
            elif value:
                html += f"<td>{value}</td>"
            else:
                html += "<td></td>"
        html += "</tr>"
    
    html += "</tbody></table>"
    
    st.markdown(html, unsafe_allow_html=True)
    
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
    
    # Create a dictionary mapping teams to their divisions
    team_division_map = {}
    for _, row in df.iterrows():
        home_team = row['Home']
        away_team = row['Away']
        division = row['Division']
        
        if pd.notna(home_team) and home_team not in team_division_map:
            team_division_map[home_team] = division
        if pd.notna(away_team) and away_team not in team_division_map:
            team_division_map[away_team] = division
    
    # Create team options with division prefix and sort
    team_options = []
    for team, division in team_division_map.items():
        team_options.append({
            'display': f"{division} - {team}",
            'team': team,
            'division': division
        })
    
    # Sort by division (convert to number for proper sorting), then by team name
    def sort_key(item):
        # Extract numeric part from division (e.g., "10U" -> 10)
        div = item['division']
        try:
            num = int(''.join(filter(str.isdigit, div)))
        except:
            num = 999  # Put non-numeric divisions at the end
        return (num, item['team'])
    
    team_options.sort(key=sort_key)
    
    # Create display list and lookup
    team_display_list = [opt['display'] for opt in team_options]
    team_lookup = {opt['display']: opt['team'] for opt in team_options}
    
    # Team selector
    selected_display = st.selectbox("Team", team_display_list)
    selected_team = team_lookup[selected_display]
    
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
    
    # Display schedule (drop the parsed date column)
    display_cols = ['Week', 'Game Date', 'Time', 'Field', 'Home', 'Away']
    st.dataframe(
        team_games[display_cols],
        use_container_width=True,
        hide_index=True
    )
    
    # Download button
    csv = team_games[display_cols].to_csv(index=False)
    st.download_button(
        "📥 Download as CSV",
        csv,
        f"{selected_team}_schedule.csv",
        "text/csv"
    )

elif page == "📋 Team vs Date Matrix":
    st.title("📋 Team vs Date Matrix")
    
    # Division filter
    selected_division = st.selectbox(
        "Division", 
        sort_divisions(df['Division'].unique())
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

elif page == "📊 Division Summary":
    st.title("📊 Division Summary")
    
    # Division filter
    selected_division = st.selectbox(
        "Division", 
        sort_divisions(df['Division'].unique())
    )
    
    # Filter games for selected division
    div_df = df[df['Division'] == selected_division].copy()
    
    # Get all teams in this division
    home_teams = div_df['Home'].dropna().unique()
    away_teams = div_df['Away'].dropna().unique()
    all_teams = sorted(set(list(home_teams) + list(away_teams)))
    
    # Create summary data for selected division only
    summary_rows = []
    
    # Add division header row
    summary_rows.append({
        'Division': selected_division,
        'Team': '',
        **{f'Week {week}': '' for week in sorted(df['Week'].unique())},
        'Grand Total': ''
    })
    
    # Track division totals per week
    division_week_totals = {}
    division_grand_total = 0
    
    # Add row for each team
    for team in all_teams:
        team_row = {
            'Division': '',
            'Team': team
        }
        
        team_total = 0
        
        # Count games per week for this team
        for week in sorted(df['Week'].unique()):
            week_games = div_df[
                ((div_df['Home'] == team) | (div_df['Away'] == team)) &
                (div_df['Week'] == week)
            ]
            count = len(week_games)
            team_row[f'Week {week}'] = count if count > 0 else ''
            team_total += count
            
            # Track for division totals
            if week not in division_week_totals:
                division_week_totals[week] = 0
            division_week_totals[week] += count
        
        team_row['Grand Total'] = team_total
        division_grand_total += team_total
        summary_rows.append(team_row)
    
    # Add division total row
    division_total_row = {
        'Division': '',
        'Team': f'{selected_division} Total'
    }
    for week in sorted(df['Week'].unique()):
        division_total_row[f'Week {week}'] = division_week_totals.get(week, '')
    division_total_row['Grand Total'] = division_grand_total
    summary_rows.append(division_total_row)
    
    # Convert to DataFrame
    summary_df = pd.DataFrame(summary_rows)
    
    # Create styled HTML table
    html = """
    <style>
        .summary-table {
            border-collapse: collapse;
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
        }
        .summary-table th, .summary-table td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        .summary-table th {
            background-color: #f0f2f6;
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .summary-table tr:hover {
            background-color: #f8f9fa;
        }
        .total-row {
            background-color: #fff3cd !important;
            font-weight: 600;
        }
        .total-column {
            background-color: #d1ecf1;
            font-weight: 600;
        }
        .total-cell {
            background-color: #ffc107 !important;
            font-weight: 700;
        }
    </style>
    <table class="summary-table">
        <thead>
            <tr>
    """
    
    # Add headers
    for col in summary_df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    
    # Add data rows
    for idx, row in summary_df.iterrows():
        is_total_row = 'Total' in str(row.get('Team', ''))
        row_class = 'total-row' if is_total_row else ''
        html += f'<tr class="{row_class}">'
        
        for col_idx, col in enumerate(summary_df.columns):
            value = row[col]
            # Check if this is the Grand Total column
            is_total_col = col == 'Grand Total'
            
            if is_total_row and is_total_col:
                cell_class = 'total-cell'
            elif is_total_col:
                cell_class = 'total-column'
            else:
                cell_class = ''
            
            html += f'<td class="{cell_class}">{value}</td>'
        
        html += "</tr>"
    
    html += "</tbody></table>"
    
    # Display the styled table
    st.markdown(html, unsafe_allow_html=True)
    
    # Download button
    csv = summary_df.to_csv(index=False)
    st.download_button(
        "📥 Download as CSV",
        csv,
        f"division_summary_{selected_division}.csv",
        "text/csv"
    )

elif page == "✏️ Edit Game*":
    st.title("✏️ Edit Game")
    
    st.markdown("""
    **Administrator Interface:** Search for a game and edit any field including 
    date, time, field, teams, division, etc.
    """)
    
    # Step 1: Search/Select a game
    st.markdown("### Step 1: Find the Game to Edit")
    
    col1, col2 = st.columns(2)
    with col1:
        search_division = st.selectbox(
            "Filter by Division", 
            ["All"] + sort_divisions(df['Division'].unique())
        )
    with col2:
        search_week = st.selectbox(
            "Filter by Week",
            ["All"] + sorted(df['Week'].unique())
        )
    
    # Filter games
    search_df = df.copy()
    if search_division != "All":
        search_df = search_df[search_df['Division'] == search_division]
    if search_week != "All":
        search_df = search_df[search_df['Week'] == search_week]
    
    # Display filtered games with Game # as identifier
    st.markdown(f"**Found {len(search_df)} games**")
    
    # Create game selection options
    game_options = []
    game_indices = []
    for idx, row in search_df.iterrows():
        game_display = f"Game #{row['Game #']} | {row['Game Date']} {row['Time']} | {row['Division']} | {row['Home']} vs {row['Away']} @ {row['Field']}"
        game_options.append(game_display)
        game_indices.append(idx)
    
    if len(game_options) == 0:
        st.info("No games found with selected filters")
    else:
        selected_game_display = st.selectbox("Game to Edit", game_options)
        selected_idx = game_indices[game_options.index(selected_game_display)]
        selected_game = df.loc[selected_idx]
        
        st.markdown("---")
        st.markdown("### Step 2: Edit Game Details")
        
        # Get all unique values for dropdowns
        all_divisions = sort_divisions(df['Division'].unique())
        all_fields = sorted(df['Field'].unique())
        all_times = sorted(df['Time'].unique())
        all_home_teams = sorted(df['Home'].dropna().unique())
        all_away_teams = sorted(df['Away'].dropna().unique())
        all_statuses = sorted(df['Status'].dropna().unique())
        all_daycodes = sorted(df['Daycode'].dropna().unique())
        all_dates = sorted(df['Game Date'].unique())
        
        # Create form with dropdowns where possible
        with st.form("edit_game_form"):
            st.markdown(f"**Editing Game #{selected_game['Game #']}**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                new_game_num = st.text_input("Game #", value=str(selected_game['Game #']))
                
                # Game Date - dropdown with all existing dates
                current_date = str(selected_game['Game Date'])
                if current_date in all_dates:
                    date_index = all_dates.index(current_date)
                else:
                    date_index = 0
                new_game_date = st.selectbox("Game Date", all_dates, index=date_index)
                
                # Field - dropdown
                current_field = str(selected_game['Field'])
                if current_field in all_fields:
                    field_index = all_fields.index(current_field)
                else:
                    field_index = 0
                new_field = st.selectbox("Field", all_fields, index=field_index)
                
                # Time - dropdown
                current_time = str(selected_game['Time'])
                if current_time in all_times:
                    time_index = all_times.index(current_time)
                else:
                    time_index = 0
                new_time = st.selectbox("Time", all_times, index=time_index)
            
            with col2:
                # Home Team - dropdown
                current_home = str(selected_game['Home'])
                if current_home in all_home_teams:
                    home_index = all_home_teams.index(current_home)
                else:
                    home_index = 0
                new_home = st.selectbox("Home Team", all_home_teams, index=home_index)
                
                # Away Team - dropdown
                current_away = str(selected_game['Away'])
                if current_away in all_away_teams:
                    away_index = all_away_teams.index(current_away)
                else:
                    away_index = 0
                new_away = st.selectbox("Away Team", all_away_teams, index=away_index)
                
                new_week = st.number_input("Week", value=int(selected_game['Week']))
                
                # Daycode - dropdown
                current_daycode = str(selected_game['Daycode'])
                if current_daycode in all_daycodes:
                    daycode_index = all_daycodes.index(current_daycode)
                else:
                    daycode_index = 0
                new_daycode = st.selectbox("Daycode", all_daycodes, index=daycode_index)
            
            with col3:
                # Division - dropdown
                current_division = str(selected_game['Division'])
                if current_division in all_divisions:
                    div_index = all_divisions.index(current_division)
                else:
                    div_index = 0
                new_division = st.selectbox("Division", all_divisions, index=div_index)
                
                new_game = st.text_input("Game", value=str(selected_game['Game']))
                new_div = st.text_input("Div", value=str(selected_game['Div']))
                
                # Status - dropdown
                current_status = str(selected_game['Status'])
                if current_status in all_statuses:
                    status_index = all_statuses.index(current_status)
                else:
                    status_index = 0
                new_status = st.selectbox("Status", all_statuses, index=status_index)
            
            # Additional fields if they exist
            col4, col5, col6 = st.columns(3)
            with col4:
                new_comment = st.text_area("Comment", value=str(selected_game.get('Comment', '')))
            with col5:
                new_original_date = st.text_input("Original Date", value=str(selected_game.get('Original Date', '')))
            
            # Submit button
            col_submit1, col_submit2 = st.columns([1, 4])
            with col_submit1:
                submitted = st.form_submit_button("💾 Save Changes", type="primary")
            with col_submit2:
                cancel = st.form_submit_button("❌ Cancel")
            
            if submitted:
                # Update the database
                conn = sqlite3.connect('wusa_schedule.db')
                cursor = conn.cursor()
                
                # Build update query
                update_query = """
                    UPDATE games SET
                        "Game #" = ?,
                        "Game Date" = ?,
                        "Field" = ?,
                        "Time" = ?,
                        "Home" = ?,
                        "Away" = ?,
                        "Week" = ?,
                        "Daycode" = ?,
                        "Division" = ?,
                        "Game" = ?,
                        "Div" = ?,
                        "Status" = ?,
                        "Comment" = ?,
                        "Original Date" = ?
                    WHERE "Game #" = ?
                """
                
                cursor.execute(update_query, (
                    new_game_num,
                    new_game_date,
                    new_field,
                    new_time,
                    new_home,
                    new_away,
                    new_week,
                    new_daycode,
                    new_division,
                    new_game,
                    new_div,
                    new_status,
                    new_comment,
                    new_original_date,
                    selected_game['Game #']  # WHERE clause
                ))
                
                conn.commit()
                conn.close()
                
                # Clear cache to reload data
                st.cache_data.clear()
                
                st.success(f"✅ Game #{new_game_num} updated successfully!")
                st.info("🔄 Page will reload with updated data...")
                st.rerun()

elif page == "📅 Teams by Day":
    st.title("📅 Teams by Day")
    
    # Division filter
    selected_division = st.selectbox(
        "Division", 
        sort_divisions(df['Division'].unique())
    )
    
    # Filter games for selected division
    div_df = df[df['Division'] == selected_division].copy()
    
    # Get all unique dates sorted
    all_dates = sorted(div_df['Game Date'].unique())
    
    # Create date format mapping (M-11/3, T-12/1, etc.) and full date names
    date_headers = {}
    date_full_names = {}
    for date_str in all_dates:
        # Parse the date
        date_obj = pd.to_datetime(date_str)
        # Get day of week abbreviation and format as M-11/3
        day_abbr = date_obj.strftime('%a')[0]  # First letter of day (M, T, W, etc.)
        month_day = date_obj.strftime('%-m/%-d')  # Month/Day without leading zeros
        short_date = f"{day_abbr}-{month_day}"
        date_headers[date_str] = short_date
        # Store full day name for tooltip
        date_full_names[short_date] = date_obj.strftime('%A')  # Monday, Tuesday, etc.
    
    # Get all teams in this division
    home_teams = div_df['Home'].dropna().unique()
    away_teams = div_df['Away'].dropna().unique()
    all_teams = sorted(set(list(home_teams) + list(away_teams)))
    
    # Create matrix data
    matrix_rows = []
    
    # Add row for each team (no division header row)
    for team in all_teams:
        team_row = {'Team': team}
        team_total = 0
        dates_with_multiple_games = 0
        
        # Count games per date for this team
        for date in all_dates:
            games_on_date = div_df[
                ((div_df['Home'] == team) | (div_df['Away'] == team)) &
                (div_df['Game Date'] == date)
            ]
            count = len(games_on_date)
            
            if count > 1:
                dates_with_multiple_games += 1
            
            team_row[date_headers[date]] = count if count > 0 else ''
            team_total += count
        
        team_row['Dates with >1 Game'] = dates_with_multiple_games if dates_with_multiple_games > 0 else ''
        team_row['Grand Total'] = team_total
        matrix_rows.append(team_row)
    
    # Convert to DataFrame
    matrix_df = pd.DataFrame(matrix_rows)
    
    # Create styled HTML table with tooltips and Grand Total column highlighting
    html = """
    <style>
        .teams-day-table {
            border-collapse: collapse;
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            font-size: 14px;
        }
        .teams-day-table th, .teams-day-table td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }
        .teams-day-table th {
            background-color: #f0f2f6;
            font-weight: 400;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .teams-day-table tr:hover {
            background-color: #f8f9fa;
        }
        .total-column {
            background-color: #d1ecf1;
            font-weight: 600;
        }
        .tooltip {
            position: relative;
            cursor: help;
        }
        .tooltip .tooltiptext {
            visibility: hidden;
            width: 120px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 5px;
            position: absolute;
            z-index: 99999;
            bottom: 125%;
            left: 50%;
            margin-left: -60px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
            pointer-events: none;
        }
        .tooltip .tooltiptext::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #333 transparent transparent transparent;
        }
        .tooltip:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
    </style>
    <table class="teams-day-table">
        <thead>
            <tr>
    """
    
    # Add headers with tooltips for date columns
    for col in matrix_df.columns:
        if col in date_full_names:
            # Date column with tooltip
            html += f'''
                <th class="tooltip">
                    {col}
                    <span class="tooltiptext">{date_full_names[col]}</span>
                </th>
            '''
        else:
            # Regular column
            html += f"<th>{col}</th>"
    
    html += "</tr></thead><tbody>"
    
    # Add data rows
    for idx, row in matrix_df.iterrows():
        html += "<tr>"
        
        for col in matrix_df.columns:
            value = row[col]
            # Check if this is the Grand Total column
            cell_class = 'total-column' if col == 'Grand Total' else ''
            html += f'<td class="{cell_class}">{value}</td>'
        
        html += "</tr>"
    
    html += "</tbody></table>"
    
    # Display the styled table using components for better rendering
    import streamlit.components.v1 as components
    components.html(html, height=600, scrolling=True)
    
    # Download button
    csv = matrix_df.to_csv(index=False)
    st.download_button(
        "📥 Download as CSV",
        csv,
        f"teams_by_day_{selected_division}.csv",
        "text/csv"
    )

elif page == "✉️ Request Change":
    st.title("✉️ Request Change")
    
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
            selected_division = st.selectbox("Division", sort_divisions(df['Division'].unique()))
        with col2:
            # Filter games by selected division
            division_games = df[df['Division'] == selected_division]
            game_options = [
                f"{row['Game Date']} - {row['Time']} - {row['Home']} vs {row['Away']}"
                for _, row in division_games.iterrows()
            ]
            selected_game = st.selectbox("Game", game_options)
        
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

elif page == "📋 View Requests*":
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