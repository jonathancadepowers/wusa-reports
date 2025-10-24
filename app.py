# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import pytz
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration (you'll need to set these in Streamlit secrets)
def send_confirmation_email(recipient_email, request_id, team, game, reason):
    """
    Send a confirmation email to the user who submitted a schedule change request.
    
    Email credentials should be stored in Streamlit secrets:
    - SMTP_SERVER
    - SMTP_PORT
    - SMTP_USERNAME
    - SMTP_PASSWORD
    - FROM_EMAIL
    """
    try:
        # Get email settings from Streamlit secrets
        smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = st.secrets.get("SMTP_PORT", 587)
        smtp_username = st.secrets.get("SMTP_USERNAME", "")
        smtp_password = st.secrets.get("SMTP_PASSWORD", "")
        from_email = st.secrets.get("FROM_EMAIL", smtp_username)
        
        # Skip if credentials not configured
        if not smtp_username or not smtp_password:
            return False, "Email credentials not configured"
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'WUSA Schedule Change Request Confirmation - #{request_id}'
        msg['From'] = from_email
        msg['To'] = recipient_email
        
        # Create HTML email body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5282;">Schedule Change Request Confirmation</h2>
                
                <p>Thank you for submitting your schedule change request to the WUSA Scheduling Team!</p>
                
                <div style="background-color: #f7fafc; border-left: 4px solid #4299e1; padding: 15px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2c5282;">Request Details:</h3>
                    <p><strong>Request ID:</strong> #{request_id}</p>
                    <p><strong>Team:</strong> {team}</p>
                    <p><strong>Game:</strong> {game}</p>
                    <p><strong>Reason:</strong> {reason}</p>
                </div>
                
                <p>Your request has been received and will be reviewed by the WUSA Scheduling Team. You will receive another email once your request has been processed.</p>
                
                <p style="color: #718096; font-size: 14px; margin-top: 30px;">
                    If you have any questions, please contact the WUSA Scheduling Team.
                </p>
                
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">
                
                <p style="color: #a0aec0; font-size: 12px;">
                    This is an automated message from the WUSA Schedule Management System.
                </p>
            </div>
        </body>
        </html>
        """
        
        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)
        
        return True, "Email sent successfully"
        
    except Exception as e:
        return False, f"Error sending email: {str(e)}"

def send_admin_notification_email(game_info, changes_list):
    """
    Send an email notification to admin when a game is edited.

    Args:
        game_info: Dictionary with game details (Game #, Division, Date, Time, Home, Away, Field)
        changes_list: List of tuples (field_name, old_value, new_value)

    Email credentials should be stored in Streamlit secrets:
    - SMTP_SERVER
    - SMTP_PORT
    - SMTP_USERNAME
    - SMTP_PASSWORD
    - FROM_EMAIL
    """
    try:
        # Get email settings from Streamlit secrets
        smtp_server = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = st.secrets.get("SMTP_PORT", 587)
        smtp_username = st.secrets.get("SMTP_USERNAME", "")
        smtp_password = st.secrets.get("SMTP_PASSWORD", "")

        # Get from/to addresses from settings (with fallbacks)
        from_email = get_setting('email_from_address', '')
        if not from_email:
            from_email = st.secrets.get("FROM_EMAIL", smtp_username)

        to_addresses = get_setting('email_to_addresses', 'jpowers@gmail.com')

        # Skip if credentials not configured
        if not smtp_username or not smtp_password:
            return False, "Email credentials not configured"

        # Skip if no recipient addresses
        if not to_addresses:
            return False, "No recipient addresses configured"

        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'WUSA Schedule - Game #{game_info["Game #"]} Updated'
        msg['From'] = from_email
        msg['To'] = to_addresses

        # Build changes table HTML
        changes_html = ""
        for field_name, old_value, new_value in changes_list:
            changes_html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;">{field_name}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #d73a49;">{old_value}</td>
                    <td style="padding: 8px; border: 1px solid #ddd; color: #28a745;">{new_value}</td>
                </tr>
            """

        # Create HTML email body
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 700px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c5282;">Game Schedule Update Notification</h2>

                <p>A game has been updated in the WUSA Schedule Management System.</p>

                <div style="background-color: #f7fafc; border-left: 4px solid #4299e1; padding: 15px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #2c5282;">Game Details:</h3>
                    <p><strong>Game #:</strong> {game_info["Game #"]}</p>
                    <p><strong>Division:</strong> {game_info["Division"]}</p>
                    <p><strong>Date:</strong> {game_info["Game Date"]}</p>
                    <p><strong>Time:</strong> {game_info["Time"]}</p>
                    <p><strong>Teams:</strong> {game_info["Home"]} vs {game_info["Away"]}</p>
                    <p><strong>Field:</strong> {game_info["Field"]}</p>
                </div>

                <h3 style="color: #2c5282;">Changes Made:</h3>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <thead>
                        <tr style="background-color: #f0f2f6;">
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Field</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Old Value</th>
                            <th style="padding: 8px; border: 1px solid #ddd; text-align: left;">New Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        {changes_html}
                    </tbody>
                </table>

                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 20px 0;">

                <p style="color: #a0aec0; font-size: 12px;">
                    This is an automated notification from the WUSA Schedule Management System.
                </p>
            </div>
        </body>
        </html>
        """

        # Attach HTML body
        msg.attach(MIMEText(html_body, 'html'))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(msg)

        return True, "Admin notification sent successfully"

    except Exception as e:
        return False, f"Error sending admin notification: {str(e)}"

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

# Database migration - add audit trail column if it doesn't exist
def ensure_audit_trail_column():
    """Ensure the game_audit_trail and last_updated columns exist in the database"""
    try:
        conn = sqlite3.connect('wusa_schedule.db')
        cursor = conn.cursor()
        
        # Check if columns exist
        cursor.execute("PRAGMA table_info(games)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'game_audit_trail' not in columns:
            cursor.execute("ALTER TABLE games ADD COLUMN game_audit_trail TEXT DEFAULT ''")
            conn.commit()
            print("Added game_audit_trail column")
        
        if 'last_updated' not in columns:
            cursor.execute("ALTER TABLE games ADD COLUMN last_updated INTEGER DEFAULT 0")
            conn.commit()
            print("Added last_updated column")
        
        # Drop schedule_requests table if it exists (no longer needed)
        cursor.execute("DROP TABLE IF EXISTS schedule_requests")
        conn.commit()
        
        conn.close()
    except Exception as e:
        print(f"Error ensuring audit trail columns: {e}")

# Database migration - create settings table if it doesn't exist
def ensure_settings_table():
    """Ensure the settings table exists in the database"""
    try:
        conn = sqlite3.connect('wusa_schedule.db')
        cursor = conn.cursor()

        # Create settings table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        # Add default values if they don't exist
        cursor.execute("SELECT key FROM settings WHERE key = 'email_from_address'")
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO settings (key, value) VALUES ('email_from_address', '')")

        cursor.execute("SELECT key FROM settings WHERE key = 'email_to_addresses'")
        if cursor.fetchone() is None:
            cursor.execute("INSERT INTO settings (key, value) VALUES ('email_to_addresses', 'jpowers@gmail.com')")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error ensuring settings table: {e}")

# Helper functions for settings
def get_setting(key, default=''):
    """Get a setting value from the database"""
    try:
        conn = sqlite3.connect('wusa_schedule.db')
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else default
    except Exception as e:
        print(f"Error getting setting {key}: {e}")
        return default

def set_setting(key, value):
    """Set a setting value in the database"""
    try:
        conn = sqlite3.connect('wusa_schedule.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value)
            VALUES (?, ?)
        """, (key, value))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error setting {key}: {e}")
        return False

# Run migrations on app startup
ensure_audit_trail_column()
ensure_settings_table()

# Helper function to add audit trail entry
def add_audit_entry(game_number, field_name, old_value, new_value):
    """
    Add an audit trail entry for a changed field.
    Returns the updated audit trail string.
    """
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    entry = {
        "timestamp": timestamp,
        "field": field_name,
        "old_value": str(old_value),
        "new_value": str(new_value)
    }
    
    return json.dumps(entry)

# Helper function to sort divisions numerically (7U, 8U, 9U, 10U, 12U, 14U)
def sort_divisions(divisions):
    def get_numeric_value(div):
        try:
            # Extract numeric part from division (e.g., "10U" -> 10)
            return int(''.join(filter(str.isdigit, str(div))))
        except:
            return 999  # Put non-numeric divisions at the end
    return sorted(divisions, key=get_numeric_value)

# Helper function to calculate Week and Daycode from Game Date
def calculate_week_and_daycode(game_date_str):
    """
    Calculate Week number and Daycode from a game date string.
    Returns tuple: (week_number, daycode)
    """
    try:
        # Parse the date
        date_obj = pd.to_datetime(game_date_str)
        
        # Calculate week number (week of year)
        week_number = date_obj.isocalendar()[1]
        
        # Calculate daycode (day of week: 1=Monday, 7=Sunday)
        # Adjust to match your convention if different
        daycode = date_obj.isocalendar()[2]  # ISO weekday: 1=Mon, 7=Sun
        
        return week_number, daycode
    except:
        # If parsing fails, return defaults
        return 0, 0

df = load_games()

# Sidebar
# Add logo at the top
st.sidebar.image("wusa_logo.png", width=int(300 * 0.50))  # 50% of a reasonable base width

st.sidebar.title("Fall 2025 Schedule")

# Single radio group with all pages
page = st.sidebar.radio(
    "",
    [
        "📅 Full Schedule",
        "🏟️ Games by Field",
        "👥 Team Schedules",
        "📋 Team vs Date Matrix",
        "📊 Division Summary",
        "📅 Teams by Day",
        "📆 Monthly Calendar",
        "🔍 Data Query Tool*",
        "✏️ Edit Game*",
        "📝 Recent Changes*",
        "⚙️ Settings*"
    ]
)

st.sidebar.markdown("*Admin Pages")

# Admin logout button (show if authenticated)
if st.session_state.get('admin_authenticated', False):
    if st.sidebar.button("🔓 Logout (Admin)"):
        st.session_state.admin_authenticated = False
        st.rerun()

# Calculate metrics
total_games = len(df)

# Calculate games remaining (games that haven't happened yet)
from datetime import datetime
import pytz

# Get current CST time
cst = pytz.timezone('America/Chicago')
now_cst = datetime.now(cst)

# Count games with date/time in the future
games_remaining = 0
for _, game in df.iterrows():
    try:
        # Combine game date and time
        game_datetime_str = f"{game['Game Date']} {game['Time']}"
        # Parse as naive datetime, then localize to CST
        game_datetime = pd.to_datetime(game_datetime_str, format='%A, %B %d, %Y %I:%M %p')
        game_datetime_cst = cst.localize(game_datetime)
        
        if game_datetime_cst > now_cst:
            games_remaining += 1
    except:
        # If parsing fails, assume game is in the future
        games_remaining += 1

# Display metrics
st.sidebar.info(f"**Total Games:** {total_games}")
st.sidebar.success(f"**Games Remaining:** {games_remaining}")

# Admin authentication
ADMIN_PASSWORD = "wusarocks"
ADMIN_PAGES = ["🔍 Data Query Tool*", "✏️ Edit Game*", "📝 Recent Changes*", "⚙️ Settings*"]

# Force authentication reset for existing sessions (one-time migration)
if 'auth_version' not in st.session_state:
    st.session_state.admin_authenticated = False
    st.session_state.auth_version = 1

def check_admin_access():
    """Check if user has authenticated for admin access"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    return st.session_state.admin_authenticated

def show_admin_login():
    """Show admin login form"""
    st.title("🔒 Admin Access Required")
    st.markdown("This page requires admin authentication.")

    with st.form("admin_login"):
        password = st.text_input("Enter admin password:", type="password")
        submitted = st.form_submit_button("Login")

        if submitted:
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("✅ Authentication successful!")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")

# Check if current page requires admin access
if page in ADMIN_PAGES:
    if not check_admin_access():
        show_admin_login()
        st.stop()  # Stop execution here if not authenticated

# Main content
if page == "📅 Full Schedule":
    st.title("📅 Full Schedule")

    # Get min and max dates from the schedule
    min_date = df['Game Date Parsed'].min().date()
    max_date = df['Game Date Parsed'].max().date()

    # Initialize session state for filters if they don't exist (all empty on first load)
    if 'filter_divisions' not in st.session_state:
        st.session_state.filter_divisions = []
    if 'filter_weeks' not in st.session_state:
        st.session_state.filter_weeks = []
    if 'filter_fields' not in st.session_state:
        st.session_state.filter_fields = []
    if 'filter_teams' not in st.session_state:
        st.session_state.filter_teams = []
    if 'filter_status' not in st.session_state:
        st.session_state.filter_status = []
    if 'filter_start_date' not in st.session_state:
        st.session_state.filter_start_date = min_date
    if 'filter_end_date' not in st.session_state:
        st.session_state.filter_end_date = max_date

    # Clear All Filters button
    if st.button("🔄 Clear All Filters"):
        # Explicitly set all widget states to empty/default values
        st.session_state.filter_divisions = []
        st.session_state.filter_weeks = []
        st.session_state.filter_fields = []
        st.session_state.filter_teams = []
        st.session_state.filter_status = []
        st.session_state.filter_start_date = min_date
        st.session_state.filter_end_date = max_date
        st.rerun()

    # Filters - now in 3 rows
    col1, col2, col3 = st.columns(3)
    with col1:
        selected_divisions = st.multiselect(
            "Division",
            sort_divisions(df['Division'].unique()),
            key='filter_divisions'
        )
    with col2:
        selected_weeks = st.multiselect(
            "Week",
            sorted(df['Week'].unique()),
            key='filter_weeks'
        )
    with col3:
        selected_fields = st.multiselect(
            "Field",
            sorted(df['Field'].unique()),
            key='filter_fields'
        )

    # Second row for team filter and date range
    col4, col5, col6 = st.columns(3)
    with col4:
        # Get all unique teams (both home and away), filtering out NaN values
        home_teams = df['Home'].dropna().unique()
        away_teams = df['Away'].dropna().unique()
        all_teams = sorted(set(list(home_teams) + list(away_teams)))

        selected_teams = st.multiselect(
            "Team (Home or Away)",
            all_teams,
            key='filter_teams'
        )
    with col5:
        start_date = st.date_input(
            "Start Date",
            min_value=min_date,
            max_value=max_date,
            key='filter_start_date'
        )
    with col6:
        end_date = st.date_input(
            "End Date",
            min_value=min_date,
            max_value=max_date,
            key='filter_end_date'
        )

    # Third row for status filter
    col7, col8, col9 = st.columns(3)
    with col7:
        selected_status = st.multiselect(
            "Status",
            sorted(df['Status'].unique()),
            key='filter_status'
        )

    # Filter data - only apply filters if values are selected
    filtered_df = df.copy()

    if selected_divisions:
        filtered_df = filtered_df[filtered_df['Division'].isin(selected_divisions)]

    if selected_weeks:
        filtered_df = filtered_df[filtered_df['Week'].isin(selected_weeks)]

    if selected_fields:
        filtered_df = filtered_df[filtered_df['Field'].isin(selected_fields)]

    if selected_teams:
        # Filter to games where the selected team is either home or away
        filtered_df = filtered_df[
            filtered_df['Home'].isin(selected_teams) |
            filtered_df['Away'].isin(selected_teams)
        ]

    if selected_status:
        filtered_df = filtered_df[filtered_df['Status'].isin(selected_status)]

    # Apply date range filter
    filtered_df = filtered_df[
        (filtered_df['Game Date Parsed'].dt.date >= start_date) &
        (filtered_df['Game Date Parsed'].dt.date <= end_date)
    ]

    # Drop the parsed date column and internal columns before displaying
    columns_to_drop = ['Game Date Parsed', 'Original Date', 'game_audit_trail', 'last_updated']
    display_df = filtered_df.drop(columns=[col for col in columns_to_drop if col in filtered_df.columns])

    # Display with editable Comment column, hiding Game # and Daycode
    edited_df = st.data_editor(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=1500,  # Much taller table to use more of the page
        disabled=[col for col in display_df.columns if col != 'Comment'],  # Only Comment is editable
        column_config={
            'Game #': None,  # Hide Game # column
            'Daycode': None  # Hide Daycode column
        },
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

elif page == "🏟️ Games by Field":
    st.title("🏟️ Games by Field")

    # Get unique dates from the schedule in chronological order
    # Sort by the parsed date column to get proper chronological order
    date_df_sorted = df[['Game Date', 'Game Date Parsed']].drop_duplicates().sort_values('Game Date Parsed')
    unique_dates = date_df_sorted['Game Date'].tolist()

    # Date selector
    selected_date = st.selectbox("Date", unique_dates)
    
    # Filter games for selected date
    date_df = df[df['Game Date'] == selected_date].copy()
    
    if len(date_df) == 0:
        st.info("No games scheduled for this date.")
    else:
        # Get all unique fields and time slots
        all_fields = sorted(date_df['Field'].unique())
        all_times = sorted(date_df['Time'].unique())
        
        # Create pivot table: Time (rows) x Field (columns), counting games
        pivot_data = []
        
        for time in all_times:
            row_data = {'Time': time}
            
            for field in all_fields:
                # Count games at this time/field combination
                game_count = len(date_df[(date_df['Time'] == time) & (date_df['Field'] == field)])
                row_data[field] = game_count if game_count > 0 else 0
            
            pivot_data.append(row_data)
        
        # Convert to DataFrame
        pivot_df = pd.DataFrame(pivot_data)
        
        # Add Grand Total column (sum of games per time slot)
        # Sum all columns except 'Time'
        numeric_cols = [col for col in pivot_df.columns if col != 'Time']
        pivot_df['Grand Total'] = pivot_df[numeric_cols].sum(axis=1)
        
        # Add Grand Total row (sum of games per field)
        totals_row = {'Time': 'Grand Total'}
        for field in all_fields:
            totals_row[field] = len(date_df[date_df['Field'] == field])
        totals_row['Grand Total'] = len(date_df)
        
        # Append totals row
        pivot_df = pd.concat([pivot_df, pd.DataFrame([totals_row])], ignore_index=True)
        
        # Replace 0 with empty string for display (except Grand Total column and row)
        for col in all_fields:
            pivot_df.loc[pivot_df.index[:-1], col] = pivot_df.loc[pivot_df.index[:-1], col].replace(0, '')
        
        # Create game details dictionary for tooltips
        game_details = {}
        for _, game_row in date_df.iterrows():
            key = (game_row['Time'], game_row['Field'])
            if key not in game_details:
                game_details[key] = []
            game_info = f"{game_row['Division']} - {game_row['Home']} vs {game_row['Away']}"
            game_details[key].append(game_info)
        
        # Generate HTML table with styling and tooltips
        html = """
        <style>
            .field-pivot-table {
                border-collapse: collapse;
                width: 100%;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 14px;
            }
            .field-pivot-table th, .field-pivot-table td {
                border: 1px solid #ddd;
                padding: 8px 12px;
                text-align: center;
            }
            .field-pivot-table th {
                background-color: #f0f2f6;
                font-weight: 600;
            }
            .field-pivot-table tr:hover {
                background-color: #f8f9fa;
            }
            .total-row {
                background-color: #fff3cd;
                font-weight: 600;
            }
            .total-column {
                background-color: #d1ecf1;
                font-weight: 600;
            }
            .total-cell {
                background-color: #ffc107;
                font-weight: 700;
            }
            .tooltip-cell {
                position: relative;
                cursor: help;
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
        <table class="field-pivot-table">
            <thead>
                <tr>
                    <th>Time</th>
        """
        
        # Add column headers
        for field in all_fields:
            html += f"<th>{field}</th>"
        html += "<th>Grand Total</th></tr></thead><tbody>"
        
        # Add data rows
        for idx, row in pivot_df.iterrows():
            is_total_row = row['Time'] == 'Grand Total'
            html += "<tr>"
            
            # Time column
            cell_class = 'total-row' if is_total_row else ''
            html += f'<th class="{cell_class}">{row["Time"]}</th>'
            
            # Field columns
            for field in all_fields:
                if is_total_row:
                    cell_class = 'total-row'
                    value = row[field] if row[field] != '' else ''
                    html += f'<td class="{cell_class}">{value}</td>'
                else:
                    value = row[field] if row[field] != '' else ''
                    
                    # Check if there are games for this time/field
                    key = (row['Time'], field)
                    if key in game_details and value != '':
                        # Create tooltip with game details
                        tooltip_content = "<br>".join([f'<div class="game-item">{game}</div>' for game in game_details[key]])
                        html += f'''<td class="tooltip-cell">
                            {value}
                            <span class="tooltiptext">{tooltip_content}</span>
                        </td>'''
                    else:
                        html += f'<td>{value}</td>'
            
            # Grand Total column
            if is_total_row:
                cell_class = 'total-cell'
            else:
                cell_class = 'total-column'
            html += f'<td class="{cell_class}">{row["Grand Total"]}</td>'
            html += "</tr>"
        
        html += "</tbody></table>"
        
        st.markdown(html, unsafe_allow_html=True)
        
        # Download button
        csv = pivot_df.to_csv(index=False)
        st.download_button(
            "📥 Download as CSV",
            csv,
            f"field_pivot_{selected_date.replace(', ', '_').replace(' ', '_')}.csv",
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
    
    # Create date format mapping (Mon-11/3, Tue-12/1, etc.)
    date_headers = {}
    for date_str in sorted(division_df['Game Date'].unique()):
        # Parse the date
        date_obj = pd.to_datetime(date_str)
        # Get day of week abbreviation and format as Mon-11/3
        day_abbr = date_obj.strftime('%a')  # Mon, Tue, Wed, etc.
        month_day = date_obj.strftime('%-m/%-d')  # Month/Day without leading zeros
        short_date = f"{day_abbr}-{month_day}"
        date_headers[date_str] = short_date
    
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
            # Use the short date format as column name
            team_row[date_headers[date]] = count if count > 0 else None
        
        # Add total games column
        team_total = len(division_df[
            (division_df['Home'] == team) | (division_df['Away'] == team)
        ])
        team_row['Total Games'] = team_total
        
        matrix_data.append(team_row)
    
    # Convert to DataFrame
    matrix_df = pd.DataFrame(matrix_data)
    
    # Calculate totals row (games per date)
    totals_row = {'Team': 'Grand Total'}
    for date in sorted(division_df['Game Date'].unique()):
        short_date = date_headers[date]
        games_on_date = len(division_df[division_df['Game Date'] == date])
        totals_row[short_date] = games_on_date
    totals_row['Total Games'] = len(division_df)
    
    # Append totals row
    matrix_df = pd.concat([matrix_df, pd.DataFrame([totals_row])], ignore_index=True)
    
    # Set Team as index
    matrix_df = matrix_df.set_index('Team')
    
    # Replace None with empty string for display, convert numbers to int
    for col in matrix_df.columns:
        matrix_df[col] = matrix_df[col].apply(lambda x: int(x) if pd.notna(x) and x != '' else '')
    
    # Generate HTML table with styling
    html = """
    <style>
        .matrix-table {
            border-collapse: collapse;
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
        }
        .matrix-table th, .matrix-table td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: center;
        }
        .matrix-table th {
            background-color: #f0f2f6;
            font-weight: 600;
        }
        .matrix-table tr:hover {
            background-color: #f8f9fa;
        }
        .total-row {
            background-color: #fff3cd;
            font-weight: 600;
        }
        .total-column {
            background-color: #d1ecf1;
            font-weight: 600;
        }
        .total-cell {
            background-color: #ffc107;
            font-weight: 700;
        }
    </style>
    <table class="matrix-table">
        <thead>
            <tr>
                <th>Team</th>
    """
    
    # Add column headers (dates)
    date_columns = [col for col in matrix_df.columns if col != 'Total Games']
    for date_col in date_columns:
        html += f"<th>{date_col}</th>"
    html += "<th>Total Games</th></tr></thead><tbody>"
    
    # Add data rows
    for team_name in matrix_df.index:
        is_total_row = team_name == 'Grand Total'
        html += "<tr>"
        
        # Team name column
        cell_class = 'total-row' if is_total_row else ''
        html += f'<th class="{cell_class}">{team_name}</th>'
        
        # Date columns
        for date_col in date_columns:
            if is_total_row:
                cell_class = 'total-row'
            else:
                cell_class = ''
            value = matrix_df.loc[team_name, date_col]
            display_value = value if value != '' else ''
            html += f'<td class="{cell_class}">{display_value}</td>'
        
        # Total Games column (highlighted differently based on row)
        if is_total_row:
            cell_class = 'total-cell'
        else:
            cell_class = 'total-column'
        total_value = matrix_df.loc[team_name, 'Total Games']
        html += f'<td class="{cell_class}">{total_value}</td>'
        html += "</tr>"
    
    html += "</tbody></table>"
    
    st.markdown(html, unsafe_allow_html=True)
    
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
    
    # Track division totals per week
    division_week_totals = {}
    division_grand_total = 0
    
    # Add row for each team (no division header row)
    for team in all_teams:
        team_row = {
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
        'Team': f'{selected_division} Total'
    }
    for week in sorted(df['Week'].unique()):
        division_total_row[f'Week {week}'] = division_week_totals.get(week, '')
    division_total_row['Grand Total'] = division_grand_total
    summary_rows.append(division_total_row)
    
    # Convert to DataFrame
    summary_df = pd.DataFrame(summary_rows)
    
    # Calculate date ranges for each week for tooltips
    week_date_ranges = {}
    for week in sorted(df['Week'].unique()):
        week_games = div_df[div_df['Week'] == week]
        if len(week_games) > 0:
            # Parse dates and get min/max
            dates = pd.to_datetime(week_games['Game Date'])
            min_date = dates.min().strftime('%-m/%-d')
            max_date = dates.max().strftime('%-m/%-d')
            week_date_ranges[week] = f"{min_date}-{max_date}"
    
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
            text-align: center;
        }
        .summary-table th:first-child, .summary-table td:first-child {
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
        .tooltip-header {
            position: relative;
            cursor: help;
        }
        .tooltip-header .tooltiptext {
            visibility: hidden;
            width: 120px;
            background-color: #333;
            color: #fff;
            text-align: center;
            border-radius: 6px;
            padding: 8px;
            position: absolute;
            z-index: 1000;
            bottom: 125%;
            left: 50%;
            margin-left: -60px;
            opacity: 0;
            transition: opacity 0.3s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            font-size: 13px;
        }
        .tooltip-header .tooltiptext::after {
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: #333 transparent transparent transparent;
        }
        .tooltip-header:hover .tooltiptext {
            visibility: visible;
            opacity: 1;
        }
    </style>
    <table class="summary-table">
        <thead>
            <tr>
    """
    
    # Add headers with tooltips for Week columns
    for col in summary_df.columns:
        if col.startswith('Week '):
            # Extract week number
            week_num = int(col.split(' ')[1])
            if week_num in week_date_ranges:
                date_range = week_date_ranges[week_num]
                html += f'''<th class="tooltip-header">{col}<span class="tooltiptext">{date_range}</span></th>'''
            else:
                html += f"<th>{col}</th>"
        else:
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
    
    # Step 1: Search/Select a game
    st.markdown("### Step 1: Find the Game to Edit")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        # Get all unique teams from both Home and Away columns
        all_teams = set(df['Home'].dropna().tolist() + df['Away'].dropna().tolist())
        
        # Create team options with "Division - Team Name" format
        team_division_map = {}
        for team in all_teams:
            # Find the division for this team (check both Home and Away)
            team_games = df[(df['Home'] == team) | (df['Away'] == team)]
            if len(team_games) > 0:
                division = team_games.iloc[0]['Division']
                team_division_map[team] = division
        
        # Create formatted team list: "Division - Team Name"
        team_list = [f"{team_division_map[team]} - {team}" for team in all_teams if team in team_division_map]
        
        # Sort by division (numerically) then by team name
        def sort_key(team_str):
            division, team_name = team_str.split(" - ", 1)
            # Extract numeric part from division (e.g., "10U" -> 10)
            try:
                div_num = int(''.join(filter(str.isdigit, division)))
            except:
                div_num = 999
            return (div_num, team_name)
        
        team_options = ["All"] + sorted(team_list, key=sort_key)
        
        search_team = st.selectbox("Team", team_options)
    with col2:
        # Start Date filter
        start_date = st.date_input(
            "Start Date",
            value=None,
            help="Filter games on or after this date"
        )
    with col3:
        # End Date filter
        end_date = st.date_input(
            "End Date",
            value=None,
            help="Filter games on or before this date"
        )
    
    # Filter games
    search_df = df.copy()
    
    # Apply team filter
    if search_team != "All":
        # Extract just the team name from "Division - Team Name"
        selected_team = search_team.split(" - ", 1)[1] if " - " in search_team else search_team
        search_df = search_df[(search_df['Home'] == selected_team) | (search_df['Away'] == selected_team)]
    
    # Apply date filters if provided
    if start_date is not None:
        search_df['Date_Parsed'] = pd.to_datetime(search_df['Game Date'])
        search_df = search_df[search_df['Date_Parsed'].dt.date >= start_date]
    
    if end_date is not None:
        if 'Date_Parsed' not in search_df.columns:
            search_df['Date_Parsed'] = pd.to_datetime(search_df['Game Date'])
        search_df = search_df[search_df['Date_Parsed'].dt.date <= end_date]
    
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
        # Check if we just saved and should preserve selection
        if 'saved_game_number' in st.session_state and st.session_state.saved_game_number:
            # Find the game in the current search results
            saved_game_num = st.session_state.saved_game_number
            
            # Try to find this game in current results
            matching_games = search_df[search_df['Game #'] == saved_game_num]
            if len(matching_games) > 0:
                # Find index in game_options
                for i, idx in enumerate(game_indices):
                    if df.loc[idx]['Game #'] == saved_game_num:
                        default_index = i
                        break
                else:
                    default_index = 0
            else:
                default_index = 0
            
            # Clear the saved game number after using it
            st.session_state.saved_game_number = None
        else:
            default_index = 0
        
        selected_game_display = st.selectbox("Game to Edit", game_options, index=default_index)
        
        # Display filtered games count after dropdown
        st.markdown(f"*Found {len(search_df)} games*")
        
        selected_idx = game_indices[game_options.index(selected_game_display)]
        
        # Reload game data from database to get latest values (in case it was just edited)
        conn = sqlite3.connect('wusa_schedule.db')
        game_num = int(df.loc[selected_idx]['Game #'])
        current_game_df = pd.read_sql(f"SELECT * FROM games WHERE \"Game #\" = {game_num}", conn)
        conn.close()
        
        if len(current_game_df) > 0:
            selected_game = current_game_df.iloc[0]
        else:
            # Fallback to cached data if database read fails
            selected_game = df.loc[selected_idx]
        
        st.markdown("---")
        st.markdown("### Step 2: Edit Game")
        
        st.markdown("*💡 Tips: Week and Daycode are automatically recalculated based on the Game Date you select. All changes to this game will be tracked in the change history below.*")
        
        # Get all unique values for dropdowns
        all_fields = sorted(df['Field'].unique())
        all_times = sorted(df['Time'].unique())
        all_home_teams = sorted(df['Home'].dropna().unique())
        all_away_teams = sorted(df['Away'].dropna().unique())
        all_statuses = sorted(df['Status'].dropna().unique())
        all_dates = sorted(df['Game Date'].unique())
        
        # Create form with dropdowns where possible
        with st.form("edit_game_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
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
                
                # Status - dropdown
                current_status = str(selected_game['Status'])
                if current_status in all_statuses:
                    status_index = all_statuses.index(current_status)
                else:
                    status_index = 0
                new_status = st.selectbox("Status", all_statuses, index=status_index)
            
            with col3:
                # Read-only fields (displayed but not editable)
                st.text_input("Division", value=str(selected_game['Division']), disabled=True)
                st.text_input("Week", value=str(selected_game['Week']), disabled=True, help="Auto-calculated from Game Date")
                st.text_input("Daycode", value=str(selected_game['Daycode']), disabled=True, help="Auto-calculated from Game Date")
            
            # Additional fields if they exist
            col4, col5, col6 = st.columns(3)
            with col4:
                new_comment = st.text_area("Comment", value=str(selected_game.get('Comment', '')))
            with col5:
                new_original_date = st.text_input("Original Date", value=str(selected_game.get('Original Date', '')))
            
            # Submit button
            col_submit = st.columns([1, 3])[0]
            with col_submit:
                submitted = st.form_submit_button("💾 Save Changes", type="primary")
            
            if submitted:
                # Convert Game # to Python int for database compatibility
                game_num = int(selected_game['Game #'])
                
                # Track all changes for audit trail and email notification
                audit_entries = []
                changes_for_email = []  # List of (field_name, old_value, new_value) tuples

                # Check each field for changes
                if new_game_date != selected_game['Game Date']:
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Game Date",
                        selected_game['Game Date'],
                        new_game_date
                    ))
                    changes_for_email.append(("Game Date", selected_game['Game Date'], new_game_date))
                
                if new_field != selected_game['Field']:
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Field",
                        selected_game['Field'],
                        new_field
                    ))
                    changes_for_email.append(("Field", selected_game['Field'], new_field))

                if new_time != selected_game['Time']:
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Time",
                        selected_game['Time'],
                        new_time
                    ))
                    changes_for_email.append(("Time", selected_game['Time'], new_time))

                if new_home != selected_game['Home']:
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Home Team",
                        selected_game['Home'],
                        new_home
                    ))
                    changes_for_email.append(("Home Team", selected_game['Home'], new_home))

                if new_away != selected_game['Away']:
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Away Team",
                        selected_game['Away'],
                        new_away
                    ))
                    changes_for_email.append(("Away Team", selected_game['Away'], new_away))

                if new_status != selected_game['Status']:
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Status",
                        selected_game['Status'],
                        new_status
                    ))
                    changes_for_email.append(("Status", selected_game['Status'], new_status))

                if new_comment != str(selected_game.get('Comment', '')):
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Comment",
                        selected_game.get('Comment', ''),
                        new_comment
                    ))
                    changes_for_email.append(("Comment", selected_game.get('Comment', ''), new_comment))

                if new_original_date != str(selected_game.get('Original Date', '')):
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Original Date",
                        selected_game.get('Original Date', ''),
                        new_original_date
                    ))
                    changes_for_email.append(("Original Date", selected_game.get('Original Date', ''), new_original_date))
                
                # Recalculate Week and Daycode based on new game date
                new_week, new_daycode = calculate_week_and_daycode(new_game_date)
                
                # Track if Week or Daycode changed (due to date change)
                if new_week != selected_game['Week']:
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Week (auto-calculated)",
                        selected_game['Week'],
                        new_week
                    ))
                    changes_for_email.append(("Week (auto-calculated)", selected_game['Week'], new_week))

                if new_daycode != selected_game['Daycode']:
                    audit_entries.append(add_audit_entry(
                        game_num,
                        "Daycode (auto-calculated)",
                        selected_game['Daycode'],
                        new_daycode
                    ))
                    changes_for_email.append(("Daycode (auto-calculated)", selected_game['Daycode'], new_daycode))
                
                # Get existing audit trail
                conn = sqlite3.connect('wusa_schedule.db')
                cursor = conn.cursor()
                
                cursor.execute("SELECT game_audit_trail FROM games WHERE \"Game #\" = ?", (game_num,))
                result = cursor.fetchone()
                existing_audit = result[0] if result and result[0] else ""
                
                # Append new entries to audit trail (newline separated JSON entries)
                if audit_entries:
                    new_audit_trail = existing_audit
                    if existing_audit:
                        new_audit_trail += "\n"
                    new_audit_trail += "\n".join(audit_entries)
                else:
                    new_audit_trail = existing_audit
                
                try:
                    # Convert Game # to Python int (numpy.int64 doesn't work with SQLite)
                    game_num = int(selected_game['Game #'])
                    
                    # Get current epoch timestamp
                    import time
                    current_timestamp = int(time.time())
                    
                    # Update the database - including recalculated Week and Daycode, audit trail, and timestamp
                    update_query = """
                        UPDATE games SET
                            "Game Date" = ?,
                            "Field" = ?,
                            "Time" = ?,
                            "Home" = ?,
                            "Away" = ?,
                            "Status" = ?,
                            "Week" = ?,
                            "Daycode" = ?,
                            "Comment" = ?,
                            "Original Date" = ?,
                            "game_audit_trail" = ?,
                            "last_updated" = ?
                        WHERE "Game #" = ?
                    """
                    
                    cursor.execute(update_query, (
                        new_game_date,
                        new_field,
                        new_time,
                        new_home,
                        new_away,
                        new_status,
                        new_week,
                        new_daycode,
                        new_comment,
                        new_original_date,
                        new_audit_trail,
                        current_timestamp,
                        game_num  # Use converted int
                    ))
                    
                    conn.commit()
                    conn.close()

                    # Send admin notification email if there were changes
                    if changes_for_email:
                        # Prepare game info for email
                        game_info = {
                            "Game #": game_num,
                            "Division": selected_game['Division'],
                            "Game Date": new_game_date,
                            "Time": new_time,
                            "Home": new_home,
                            "Away": new_away,
                            "Field": new_field
                        }

                        # Send email notification
                        email_success, email_message = send_admin_notification_email(game_info, changes_for_email)

                        if email_success:
                            success_msg = "✅ Changes saved, audit log updated, and notification email sent."
                        else:
                            success_msg = f"✅ Changes saved and audit log updated. (Email notification failed: {email_message})"
                    else:
                        success_msg = "✅ No changes were made."

                    # Clear cache to reload data
                    st.cache_data.clear()

                    # Store success message in session state
                    st.session_state.edit_success_message = success_msg

                    st.session_state.just_saved = True
                    st.session_state.saved_game_number = game_num

                    # Reload the page to show updated data
                    st.rerun()
                        
                except Exception as e:
                    conn.close()
                    st.error(f"❌ Error updating game: {str(e)}")
                    st.error(f"Debug info: Game # = {game_num}")
        
        # Show success message if it exists from previous save
        if 'edit_success_message' in st.session_state:
            if st.session_state.edit_success_message.startswith("✅"):
                st.success(st.session_state.edit_success_message)
            else:
                st.info(st.session_state.edit_success_message)
            # Clear the message so it doesn't show again
            del st.session_state.edit_success_message
        
        # Show audit trail after the form (outside the form block)
        st.markdown("---")
        st.markdown("### 📜 Selected Game's Change History")
        
        # Always get fresh data from database (not cached) to show latest changes
        conn = sqlite3.connect('wusa_schedule.db')
        # Use a direct query without caching
        cursor = conn.cursor()
        game_num = int(selected_game['Game #'])
        cursor.execute("SELECT game_audit_trail FROM games WHERE \"Game #\" = ?", (game_num,))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0]:
            audit_trail = result[0]
            
            if audit_trail and str(audit_trail).strip():
                import json
                
                audit_lines = str(audit_trail).strip().split('\n')
                audit_data = []
                
                for line in audit_lines:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            audit_data.append(entry)
                        except:
                            pass
                
                if audit_data:
                    # Display as a table
                    audit_df = pd.DataFrame(audit_data)
                    # Reverse order to show most recent first
                    audit_df = audit_df.iloc[::-1].reset_index(drop=True)
                    
                    st.dataframe(
                        audit_df[['timestamp', 'field', 'old_value', 'new_value']],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            'timestamp': 'Date/Time',
                            'field': 'Field Changed',
                            'old_value': 'Old Value',
                            'new_value': 'New Value'
                        }
                    )
                else:
                    st.info("No changes have been made to this game yet.")
            else:
                st.info("No changes have been made to this game yet.")
        else:
            st.info("No changes have been made to this game yet.")

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
    
    # Create date format mapping (M-11/3, T-12/1, etc.) with day name in header
    date_headers = {}
    for date_str in all_dates:
        # Parse the date
        date_obj = pd.to_datetime(date_str)
        # Get day of week abbreviation and format as Mon-11/3, Tue-12/1, etc.
        day_abbr = date_obj.strftime('%a')  # Mon, Tue, Wed, etc.
        month_day = date_obj.strftime('%-m/%-d')  # Month/Day without leading zeros
        short_date = f"{day_abbr}-{month_day}"
        date_headers[date_str] = short_date
    
    # Get all teams in this division
    home_teams = div_df['Home'].dropna().unique()
    away_teams = div_df['Away'].dropna().unique()
    all_teams = sorted(set(list(home_teams) + list(away_teams)))
    
    # Create matrix data
    matrix_rows = []
    
    # Add row for each team
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
    
    # Replace empty strings with None, then fillna for display
    matrix_df = matrix_df.replace('', None).fillna('')
    
    # Generate HTML table with styling
    html = """
    <style>
        .teams-by-day-table {
            border-collapse: collapse;
            width: 100%;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            font-size: 14px;
        }
        .teams-by-day-table th, .teams-by-day-table td {
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: center;
        }
        .teams-by-day-table th:first-child, .teams-by-day-table td:first-child {
            text-align: left;
        }
        .teams-by-day-table th {
            background-color: #f0f2f6;
            font-weight: 600;
        }
        .teams-by-day-table tr:hover {
            background-color: #f8f9fa;
        }
        .total-column {
            background-color: #d1ecf1;
            font-weight: 600;
        }
    </style>
    <table class="teams-by-day-table">
        <thead>
            <tr>
    """
    
    # Add column headers
    for col in matrix_df.columns:
        html += f"<th>{col}</th>"
    html += "</tr></thead><tbody>"
    
    # Add data rows
    for idx, row in matrix_df.iterrows():
        html += "<tr>"
        
        for col in matrix_df.columns:
            value = row[col]
            display_value = value if value != '' else ''
            
            # Apply total column styling to Grand Total column
            if col == 'Grand Total':
                cell_tag = 'td' if col != 'Team' else 'td'
                html += f'<{cell_tag} class="total-column">{display_value}</{cell_tag}>'
            else:
                if col == 'Team':
                    html += f'<td>{display_value}</td>'
                else:
                    html += f'<td>{display_value}</td>'
        
        html += "</tr>"
    
    html += "</tbody></table>"
    
    st.markdown(html, unsafe_allow_html=True)
    
    # Download button
    csv = matrix_df.to_csv(index=False)
    st.download_button(
        "📥 Download as CSV",
        csv,
        f"teams_by_day_{selected_division}.csv",
        "text/csv"
    )

elif page == "📆 Monthly Calendar":
    st.title("📆 Monthly Calendar")
    
    import calendar
    from calendar import monthrange
    
    # Get all dates and count games per date
    df['Date_Parsed'] = pd.to_datetime(df['Game Date'])
    date_counts = df.groupby(df['Date_Parsed'].dt.date).size().to_dict()
    
    # Get available months
    available_months = sorted(df['Date_Parsed'].dt.to_period('M').unique())
    month_options = [f"{period.strftime('%B %Y')}" for period in available_months]
    
    # Determine default month - current month if it has games, otherwise earliest month
    from datetime import datetime
    current_date = datetime.now()
    current_period = pd.Period(current_date, freq='M')
    
    # Check if current month is in available months
    if current_period in available_months:
        default_month = f"{current_period.strftime('%B %Y')}"
    else:
        # Use earliest available month
        default_month = month_options[0] if month_options else None
    
    # Get the index for default selection
    default_index = month_options.index(default_month) if default_month in month_options else 0
    
    # Show tip before month selector
    st.markdown("*💡 Tip: Click a date on the calendar to view games for that day.*")
    
    # Month selector
    if len(month_options) > 0:
        selected_month_str = st.selectbox("Month", month_options, index=default_index)
        
        # Parse selected month
        selected_period = pd.Period(selected_month_str, freq='M')
        selected_year = selected_period.year
        selected_month = selected_period.month
        
        # Generate calendar
        cal = calendar.monthcalendar(selected_year, selected_month)
        month_name = calendar.month_name[selected_month]
        
        # Add custom CSS for calendar styling
        st.markdown("""
        <style>
            /* Calendar cell borders and consistent height */
            div[data-testid="column"] {
                border: 1px solid #ddd;
                padding: 0.5rem;
                min-height: 120px;
                max-height: 120px;
                display: flex;
                flex-direction: column;
            }
            
            /* Style for day buttons - consistent height */
            .stButton button {
                width: 100%;
                min-height: 100px !important;
                max-height: 100px !important;
                position: relative;
                white-space: pre-line;
            }
            
            /* Make the word "Games:" appear in red - targeting button text */
            .stButton button p {
                color: inherit;
            }
            
            /* Non-game day cells */
            .calendar-day-empty {
                height: 100px;
                border: 1px solid #ddd;
                background-color: #f8f9fa;
            }
            
            .calendar-day-no-games {
                text-align: center;
                padding: 2rem;
                color: #999;
                font-size: 18px;
                font-weight: 600;
                border: 1px solid #ddd;
                min-height: 100px;
                max-height: 100px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Create calendar using Streamlit columns
        # Header row
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        header_cols = st.columns(7)
        for idx, day_name in enumerate(day_names):
            with header_cols[idx]:
                st.markdown(f"<div style='text-align: center; font-weight: 600; padding: 0.5rem; border: 1px solid #ddd; background-color: #f0f2f6;'>{day_name}</div>", unsafe_allow_html=True)
        
        # Add spacing after header
        st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
        
        # Calendar rows
        for week_idx, week in enumerate(cal):
            week_cols = st.columns(7)
            for idx, day in enumerate(week):
                with week_cols[idx]:
                    if day == 0:
                        # Empty day
                        st.markdown("<div class='calendar-day-empty'></div>", unsafe_allow_html=True)
                    else:
                        date_obj = datetime(selected_year, selected_month, day).date()
                        game_count = date_counts.get(date_obj, 0)
                        
                        if game_count > 0:
                            # Create a button for days with games with colored game count
                            # Note: Streamlit doesn't support HTML in button labels, so we'll format it with line breaks
                            button_label = f"{day}\n\n:red[Games: {game_count}]"
                            
                            if st.button(
                                button_label,
                                key=f"cal_{date_obj}",
                                use_container_width=True,
                                type="primary" if st.session_state.get('selected_calendar_date') == date_obj else "secondary"
                            ):
                                st.session_state.selected_calendar_date = date_obj
                                st.rerun()
                        else:
                            # Just show the day number for days without games
                            st.markdown(f"<div class='calendar-day-no-games'>{day}</div>", unsafe_allow_html=True)
            
            # Add spacing between rows (except after last row)
            if week_idx < len(cal) - 1:
                st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Show games for selected date
        if 'selected_calendar_date' in st.session_state:
            selected_date = st.session_state.selected_calendar_date
            
            # Make sure the selected date is in this month
            if (selected_date.year == selected_year and selected_date.month == selected_month 
                and selected_date in date_counts and date_counts[selected_date] > 0):
                
                st.markdown(f"### Games on {pd.Timestamp(selected_date).strftime('%A, %B %d, %Y')}")
                
                # Filter games for selected date
                date_games = df[df['Date_Parsed'].dt.date == selected_date].copy()
                
                # Display games without Game # column
                display_cols = ['Division', 'Time', 'Field', 'Home', 'Away']
                st.dataframe(
                    date_games[display_cols],
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.warning("No games found in the schedule.")

elif page == "🔍 Data Query Tool*":
    st.title("🔍 Data Query Tool")
    
    st.markdown("""
    **Run SQL queries against the schedule database.** This tool is read-only for safety.
    """)
    
    # SQL query input
    query = st.text_area(
        "",
        height=150,
        placeholder="SELECT * FROM games LIMIT 10;",
        help="Only SELECT queries are allowed. INSERT, UPDATE, DELETE, DROP, etc. are blocked.",
        label_visibility="collapsed"
    )
    
    # Put buttons in columns to control placement
    col1, col2, col3 = st.columns([0.8, 1.2, 10])
    with col1:
        run_button = st.button("▶️ Run Query", type="primary")
    with col2:
        if st.button("📋 Example Queries"):
            st.session_state.show_examples = not st.session_state.get('show_examples', False)
    
    # Show example queries
    if st.session_state.get('show_examples', False):
        st.markdown("""
        **Example Queries:**
        
        ```sql
        -- List all tables in the database
        SELECT name FROM sqlite_master WHERE type='table';
        
        -- Show structure of the 'games' table
        PRAGMA table_info(games);
        
        -- Get all games for a specific team
        SELECT * FROM games WHERE Home = 'Aliens' OR Away = 'Aliens';
        
        -- Count games by division
        SELECT Division, COUNT(*) as game_count FROM games GROUP BY Division;
        
        -- Find games on a specific date
        SELECT * FROM games WHERE "Game Date" = 'Monday, October 13, 2025';
        
        -- Get all games at a specific field
        SELECT * FROM games WHERE Field = 'SC3';
        
        -- Count games by week
        SELECT Week, COUNT(*) as games FROM games GROUP BY Week ORDER BY Week;
        ```
        """)
    
    if run_button and query.strip():
        # Validate query is read-only
        query_upper = query.strip().upper()
        
        # Check for dangerous operations
        dangerous_keywords = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'ALTER', 'CREATE', 
                              'TRUNCATE', 'REPLACE', 'MERGE', 'GRANT', 'REVOKE']
        
        is_safe = True
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                is_safe = False
                st.error(f"❌ Query blocked: '{keyword}' operations are not allowed. Only SELECT and PRAGMA queries are permitted.")
                break
        
        if is_safe:
            # Check it starts with SELECT or PRAGMA
            if not (query_upper.strip().startswith('SELECT') or query_upper.strip().startswith('PRAGMA')):
                st.error("❌ Query must start with SELECT or PRAGMA. Only read-only queries are allowed.")
            else:
                try:
                    # Execute the query
                    conn = sqlite3.connect('wusa_schedule.db')
                    result_df = pd.read_sql(query, conn)
                    conn.close()
                    
                    # Display results
                    st.success(f"✅ Query executed successfully! Found {len(result_df)} rows.")
                    
                    # Show results
                    st.dataframe(
                        result_df,
                        use_container_width=True,
                        hide_index=True
                    )
                    
                    # Download button
                    csv = result_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Results as CSV",
                        csv,
                        "query_results.csv",
                        "text/csv"
                    )
                    
                except Exception as e:
                    st.error(f"❌ Query error: {str(e)}")
                    st.markdown("**Tips:**")
                    st.markdown("- Check your SQL syntax")
                    st.markdown("- Make sure table and column names are correct")
                    st.markdown("- Use double quotes for column names with spaces: `\"Game Date\"`")

elif page == "📝 Recent Changes*":
    st.title("📝 Recent Changes")
    
    # Get games that have been edited (last_updated > 0)
    conn = sqlite3.connect('wusa_schedule.db')
    
    # Check if last_updated column exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(games)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'last_updated' not in columns:
        st.info("No changes tracked yet. The change tracking system will start working after the next game edit.")
        conn.close()
    else:
        # Load games with audit trails
        edited_games_df = pd.read_sql("""
            SELECT * FROM games 
            WHERE game_audit_trail IS NOT NULL AND game_audit_trail != ''
            ORDER BY last_updated DESC
        """, conn)
        conn.close()
        
        if len(edited_games_df) == 0:
            st.info("No games have been edited yet.")
        else:
            # Parse all audit entries from all games
            import json
            all_changes = []
            
            for _, game in edited_games_df.iterrows():
                audit_trail = game['game_audit_trail']
                
                if audit_trail and str(audit_trail).strip():
                    audit_lines = str(audit_trail).strip().split('\n')
                    
                    for line in audit_lines:
                        if line.strip():
                            try:
                                entry = json.loads(line)
                                # Add game context to each change
                                game_display = f"{game['Division']} - {game['Game Date']} - {game['Time']} - {game['Home']} vs {game['Away']}"
                                
                                all_changes.append({
                                    'Last Updated': entry['timestamp'],
                                    'Game': game_display,
                                    'Field Changed': entry['field'],
                                    'Old Value': entry['old_value'],
                                    'New Value': entry['new_value']
                                })
                            except:
                                pass
            
            if len(all_changes) == 0:
                st.info("No detailed change history available.")
            else:
                # Convert to DataFrame
                changes_df = pd.DataFrame(all_changes)
                
                # Convert timestamp string to datetime for proper sorting
                changes_df['timestamp_dt'] = pd.to_datetime(changes_df['Last Updated'])
                
                # Sort by datetime descending (most recent first)
                changes_df = changes_df.sort_values('timestamp_dt', ascending=False).reset_index(drop=True)
                
                # Format timestamp for display in user's locale
                # Use DatetimeColumn which automatically displays in user's browser timezone
                
                st.markdown(f"*Showing {len(all_changes)} changes across {len(edited_games_df)} games*")
                
                # Display the table
                st.dataframe(
                    changes_df[['timestamp_dt', 'Game', 'Field Changed', 'Old Value', 'New Value']],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        'timestamp_dt': st.column_config.DatetimeColumn(
                            'Last Updated',
                            format="YYYY-MM-DD HH:mm:ss",
                            timezone='local'
                        ),
                        'Game': st.column_config.TextColumn('Game', width='large'),
                        'Field Changed': st.column_config.TextColumn('Field Changed', width='medium'),
                        'Old Value': st.column_config.TextColumn('Old Value', width='medium'),
                        'New Value': st.column_config.TextColumn('New Value', width='medium')
                    },
                    height=600
                )

elif page == "⚙️ Settings*":
    st.title("⚙️ Settings")

    # Show success message if it exists from previous save
    if 'settings_success_message' in st.session_state:
        st.success(st.session_state.settings_success_message)
        # Clear the message so it doesn't show again
        del st.session_state.settings_success_message

    # Load current settings
    current_from = get_setting('email_from_address', '')
    current_to = get_setting('email_to_addresses', 'jpowers@gmail.com')

    with st.form("email_settings_form", border=False):
        # Email Notification Settings Section
        with st.container(border=True):
            st.markdown("### 📧 Edit Game Notification Settings")
            st.markdown("When a game is edited, an email is sent from/to the addresses defined below.")

            from_address = st.text_input(
                "From Address",
                value=current_from,
                placeholder="notifications@example.com",
                help="The email address that will appear in the 'From' field of notification emails. This should typically match your SMTP username. If left blank, the system will use your SMTP username from secrets."
            )

            to_addresses = st.text_input(
                "To Addresses",
                value=current_to,
                placeholder="admin1@example.com, admin2@example.com",
                help="Email addresses that will receive notifications when games are edited. Enter one or more addresses separated by commas (e.g., admin@example.com, manager@example.com). All listed addresses will receive a copy of each notification."
            )

        # Submit button outside the container
        submitted = st.form_submit_button("💾 Save Settings", type="primary")

        if submitted:
            # Validate email addresses
            errors = []

            # Helper function for better email validation
            def is_valid_email(email):
                email = email.strip()
                if not email:
                    return False
                # Basic email validation
                if '@' not in email or '.' not in email.split('@')[1]:
                    return False
                # Check for invalid characters at start/end
                if email.startswith((',', '.', '@')) or email.endswith((',', '.', '@')):
                    return False
                return True

            # Validate from address
            if from_address and not is_valid_email(from_address):
                errors.append("From Address must be a valid email address")

            # Validate to addresses
            if to_addresses:
                # Check for trailing comma
                if to_addresses.strip().endswith(','):
                    errors.append("To Addresses cannot end with a comma. Please add an email address after the comma or remove it.")

                to_list = [email.strip() for email in to_addresses.split(',')]
                for email in to_list:
                    if email and not is_valid_email(email):
                        errors.append(f"Invalid email address: {email}")

                # Check if all emails are empty (just commas)
                valid_emails = [email for email in to_list if email]
                if not valid_emails:
                    errors.append("To Addresses must contain at least one valid email address")
            else:
                errors.append("To Addresses cannot be empty")

            if errors:
                for error in errors:
                    st.error(f"❌ {error}")
            else:
                # Save settings (strip any trailing/leading whitespace)
                set_setting('email_from_address', from_address.strip())
                set_setting('email_to_addresses', to_addresses.strip())

                # Store success message in session state
                st.session_state.settings_success_message = "✅ Settings saved successfully!"
                st.rerun()