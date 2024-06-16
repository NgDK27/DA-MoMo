import streamlit as st
import pandas as pd
import altair as alt

# Set page config
st.set_page_config(
    page_title="MoMo Topup 2020",
    layout="wide"
)

alt.themes.enable("dark")

# Load the data
file_path = "D:/New Download/MoMo Talent 2024 - Test - Data Analytics Trainee/MoMo Talent 2024_DA_Case Study Round_Questions.xlsx"
transactions_df = pd.read_excel(file_path, sheet_name='Data Transactions')
commission_df = pd.read_excel(file_path, sheet_name='Data Commission')
user_info_df = pd.read_excel(file_path, sheet_name='Data User_Info')

# Check for missing values in all three DataFrames except for 'Purchase_status' in Transactions
missing_values_transactions = transactions_df.drop(columns=['Purchase_status']).isnull().sum()
missing_values_commission = commission_df.isnull().sum()
missing_values_user_info = user_info_df.isnull().sum()

# Clean the inconsistencies in 'Location' and 'Gender' columns
user_info_df['Location'] = user_info_df['Location'].replace({
    'Ho Chi Minh City': 'HCMC',
    'Other': 'Other Cities',
    'Unknown': 'Other Cities'
})

user_info_df['Gender'] = user_info_df['Gender'].replace({
    'Nữ': 'Female',
    'female': 'Female',
    'f': 'Female',
    'FEMALE': 'Female',
    'M': 'Male',
    'MALE': 'Male',
    'Nam': 'Male',
    'male': 'Male'
})

# Function to correct non-20xx dates to 20xx
def correct_year_string(date_str):
    if not date_str.startswith('20'):
        return '20' + date_str[2:]
    return date_str

# Apply the function to the 'First_tran_date' column
user_info_df['First_tran_date'] = user_info_df['First_tran_date'].astype(str).apply(correct_year_string)

# Fill in missing values in 'Purchase_status' with 'Standard'
transactions_df['Purchase_status'] = transactions_df['Purchase_status'].fillna('Standard')

# Convert 'Amount' to numeric values
transactions_df['Amount'] = transactions_df['Amount'].str.replace(',', '').astype(float)

# Merge the Transactions and Commission DataFrames on 'Merchant_id' to get the commission rates
transactions_with_commission_df = pd.merge(transactions_df, commission_df, on='Merchant_id', how='left')

# Calculate the revenue for each transaction and add it as a new column 'Revenue'
transactions_with_commission_df['Revenue'] = (transactions_with_commission_df['Amount'] * transactions_with_commission_df['Rate_pct']) / 100

# Drop unnecessary columns from the transactions DataFrame
transactions_df = transactions_with_commission_df.drop(columns=["Merchant_name", 'Merchant_id', "Rate_pct"])

# Function to parse dates correctly
def parse_date(date):
    try:
        return pd.to_datetime(date, format='%Y-%m-%d', errors='coerce')
    except:
        return pd.to_datetime(date, format='%d/%m/%Y', errors='coerce')

# Apply the function to the 'Date' column in transactions_df and 'First_tran_date' column in user_info_df
transactions_df['Date'] = transactions_df['Date'].apply(parse_date)
user_info_df['First_tran_date'] = user_info_df['First_tran_date'].apply(parse_date)

# Merge the user_info_df with transactions_df to get the additional columns
transactions_with_user_info_df = pd.merge(transactions_df, user_info_df[['User_id', 'Age', 'Gender', 'Location', 'First_tran_date']], left_on='user_id', right_on='User_id', how='left')

# Create 'Type_user' column in transactions_with_user_info_df
transactions_with_user_info_df['Type_user'] = transactions_with_user_info_df.apply(
    lambda row: 'New' if (row['Date'].year == row['First_tran_date'].year and row['Date'].month == row['First_tran_date'].month) else 'Current',
    axis=1
)

# Group by 'First_tran_date' to find the number of new users each month in 2020
new_users_2020 = transactions_with_user_info_df[transactions_with_user_info_df['Type_user'] == 'New']
new_users_2020 = new_users_2020[new_users_2020['First_tran_date'].dt.year == 2020]
monthly_new_users_2020 = new_users_2020.groupby(new_users_2020['First_tran_date'].dt.to_period('M')).agg({'user_id': 'nunique'}).reset_index()
monthly_new_users_2020['First_tran_date'] = monthly_new_users_2020['First_tran_date'].dt.to_timestamp()
monthly_new_users_2020.rename(columns={'user_id': 'New Users'}, inplace=True)


col1, col2, col3 = st.columns(3, gap='medium')

with col1:
    st.subheader("Total Revenue per Month")
    # Create Total Revenue per Month chart
    total_revenue_chart = alt.Chart(transactions_with_commission_df).mark_bar().encode(
        x='month(Date):T',
        y='sum(Revenue):Q'
    ).properties(
        width='container',
        height=300
    )
    st.altair_chart(total_revenue_chart, use_container_width=True)

with col2:
    st.subheader("Monthly Transactions Count")
    # Create Monthly Transactions Count chart
    monthly_transactions_chart = alt.Chart(transactions_with_commission_df).mark_bar().encode(
        x='month(Date):T',
        y='count(order_id):Q'
    ).properties(
        width='container',
        height=300
    )
    st.altair_chart(monthly_transactions_chart, use_container_width=True)

with col3:
    st.subheader("Average Transaction Value per Month")
    # Create Average Transaction Value per Month chart
    avg_transaction_value_chart = alt.Chart(transactions_with_commission_df).mark_bar().encode(
        x='month(Date):T',
        y='mean(Amount):Q'
    ).properties(
        width='container',
        height=300
    )
    st.altair_chart(avg_transaction_value_chart, use_container_width=True)

col4, col5, col6 = st.columns((2.5, 2, 2.5), gap='medium')

with col4:
    st.subheader("Revenue by Merchant")
    # Create Revenue by Merchant chart
    revenue_by_merchant_chart = alt.Chart(transactions_with_commission_df).mark_bar().encode(
        x='Merchant_name:N',
        y='sum(Revenue):Q'
    ).properties(
        width='container',
        height=300
    )
    st.altair_chart(revenue_by_merchant_chart, use_container_width=True)

with col5:
    st.subheader("Revenue by Purchase Status")
    # Create Revenue by Purchase Status chart
    purchase_status_summary = transactions_with_commission_df.groupby('Purchase_status')['Revenue'].sum().reset_index()
    purchase_status_summary['Percentage'] = (purchase_status_summary['Revenue'] / purchase_status_summary['Revenue'].sum()) * 100
    revenue_by_purchase_status_chart = alt.Chart(purchase_status_summary).mark_arc().encode(
        theta=alt.Theta(field='Percentage', type='quantitative'),
        color=alt.Color(field='Purchase_status', type='nominal'),
        tooltip=['Purchase_status:N', 'Percentage:Q']
    ).properties(
        width='container',
        height=300
    )
    st.altair_chart(revenue_by_purchase_status_chart, use_container_width=True)

with col6:
    st.subheader("Daily Revenue Trends")
    # Create Daily Revenue Trends chart
    daily_revenue_trends_chart = alt.Chart(transactions_with_commission_df).mark_bar().encode(
        x='day(Date):T',
        y='mean(Revenue):Q'
    ).properties(
        width='container',
        height=300
    )
    st.altair_chart(daily_revenue_trends_chart, use_container_width=True)


col7, col8 = st.columns((2, 2), gap='medium')

with col7:
    st.subheader("User Demographics")
    # Create User Demographics charts (example: Gender distribution)
    gender_distribution_chart = alt.Chart(user_info_df).mark_bar().encode(
        x='Gender:N',
        y='count(User_id):Q'
    ).properties(
        width='container',
        height=300
    )
    st.altair_chart(gender_distribution_chart, use_container_width=True)


with col8:
    st.subheader("Total number of new users")
    # Create chart for the total number of new users each month in 2020
    new_users_chart = alt.Chart(monthly_new_users_2020).mark_bar().encode(
        x=alt.X('month(First_tran_date):T', title='Date (month)', timeUnit='month'),
        y=alt.Y('New Users:Q', title='Sum of New Users')
    ).properties(
        title='Total Number of New Users Each Month in 2020',
        width='container',
        height=300
    )

    # Display the chart in Streamlit
    st.altair_chart(new_users_chart, use_container_width=True)