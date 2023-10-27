#!/Library/Frameworks/Python.framework/Versions/3.11/bin/python3

#==============================================================================
#title           :irr.py
#description     :
#author          :Eugene
#date            :20/10/2023 14:42:26
#version         :
#usage           :
#notes           :Most people prioritise profit over passion
#python_version  :3.11.1
#==============================================================================

import math
import pandas as pd
import numpy_financial as npf
from datetime import datetime
import numpy as np

#------------------------------------------------------------------------------
#                     ----    Define variables ----
#------------------------------------------------------------------------------

prepay_df = pd.read_csv('Prepay.csv')
charged_off_df = pd.read_csv('Charged_off.csv')


# Define the initial data
data = {
    'Valuation_Date': '12/31/2017',
    'Grade': 'C4',
    'Issue_Date': '8/24/2015',
    'Term': 36.00,
    'CouponRate': '28.0007632124385%',
    'Invested': '$7,500.00',
    'Outstanding_Balance': '$3,228.61',
    'Recovery_Rate': 0.08,
    'Purchase_Premium': '5.1422082%',
    'Servicing_Fee': '2.50%',
    'Earnout_Fee': '2.50%',
    'Default_Multiplier': 1.000,
    'Prepay_Multiplier': 1.000,
    'Product_Pos': 66,
    'Default_Rate': 0.03,  # Add the Default_Rate value here
}


# Get the column name from the numeric Product_Pos value:
column_index = data['Product_Pos']
column_name = charged_off_df.columns[column_index]


# Create a DataFrame
df = pd.DataFrame([data])

# Convert date strings to datetime objects
df['Valuation_Date'] = pd.to_datetime(df['Valuation_Date'])
df['Issue_Date'] = pd.to_datetime(df['Issue_Date'])

# Remove dollar signs and percentage symbols and convert to float
df['Invested'] = df['Invested'].replace('[\$,]', '', regex=True).astype(float)
df['Outstanding_Balance'] = df['Outstanding_Balance'].replace('[\$,]', '', regex=True).astype(float)
df['CouponRate'] = df['CouponRate'].replace('%', '', regex=True).astype(float)
df['Purchase_Premium'] = df['Purchase_Premium'].replace('%', '', regex=True).astype(float)
df['Servicing_Fee'] = df['Servicing_Fee'].replace('%', '', regex=True).astype(float)
df['Earnout_Fee'] = df['Earnout_Fee'].replace('%', '', regex=True).astype(float)

# Define payment parameters
monthly_coupon_rate = df['CouponRate'].values[0] / 12 / 100
monthly_payment = df['Invested'].values[0] * monthly_coupon_rate
annual_interest_rate = df['CouponRate'].values[0] / 100
monthly_interest_rate = annual_interest_rate / 12
num_periods = df['Term'].values[0]

# Create a range of dates for payments
start_date = df['Valuation_Date'].values[0]
end_date = start_date + pd.DateOffset(months=int(df['Term'].values[0]))
payment_dates = pd.date_range(start=start_date, end=end_date, freq='M')


payment_data = {
    'Months': range(1, len(payment_dates) + 1),
    'Paymnt_Count': len(payment_dates),
    'Paydate': payment_dates,
    'Scheduled_Principal': [0] * len(payment_dates),
    'Scheduled_Interest': [0] * len(payment_dates),
    'Scheduled_Balance': [0] * len(payment_dates),
    'Prepay_Speed': [0] * len(payment_dates),
    'Default_Rate': [0] * len(payment_dates),
    'Recovery': [0] * len(payment_dates),
    'Servicing_CF': [0] * len(payment_dates),
    'Earnout_CF': [0] * len(payment_dates),
    'Balance': [0] * len(payment_dates),
    'Principal': [0] * len(payment_dates),
    'Default': [0] * len(payment_dates),
    'Prepay': [0] * len(payment_dates),
    'Interest_Amount': [0] * len(payment_dates),
    'Total_CF': [0] * len(payment_dates),
}

#------------------------------------------------------------------------------
#                     ----  Create  DataFrame   ----
#------------------------------------------------------------------------------

# Create the DataFrame
payment_df = pd.DataFrame(payment_data)

# Convert data types
data_types = {
    'Months': int,
    'Paymnt_Count': int,
    'Paydate': 'datetime64[ns]',
    'Scheduled_Principal': float,
    'Scheduled_Interest': float,
    'Scheduled_Balance': float,
    'Prepay_Speed': float,
    'Default_Rate': float,
    'Recovery': float,
    'Servicing_CF': float,
    'Earnout_CF': float,
    'Balance': float,
    'Principal': float,
    'Default': float,
    'Prepay': float,
    'Interest_Amount': float,
    'Total_CF': float,
}

for col, dtype in data_types.items():
    payment_df[col] = payment_df[col].astype(dtype)

# Calculate the 'Paymnt_Count' column as described
payment_df['Paymnt_Count'] = payment_df['Months'] - 1
payment_df.loc[0, 'Paymnt_Count'] = 0  # Set the first row to 0

# Calculate the 'Paydate' column based on the provided formula
payment_df['Paydate'] = payment_df.apply(
    lambda row: df['Issue_Date'] if row['Months'] == 1 else (df['Issue_Date'] + pd.DateOffset(months=row['Months'] - 1)),
    axis=1
)

# Round like excel:
def round_down(value, decimals=2):
    multiplier = 10 ** decimals
    return math.floor(value * multiplier) / multiplier

def bankers_round(n, decimals=0):
    multiplier = 10 ** decimals
    result = int(n * multiplier)

    if abs(n * multiplier) - abs(result) == 0.5:
        # If the number is exactly halfway between two others, round to the nearest even number.
        return (result + (result % 2)) / multiplier
    return round(n, decimals)


#------------------------------------------------------------------------------
#                     ----    Calculate Default_Rate  ----
#------------------------------------------------------------------------------

# Merge payment_df with charged_off_df using the 'Months' column as a key:
merged_df = payment_df.merge(charged_off_df[['Age', column_name]], left_on='Months', right_on='Age', how='left')

# Assign the merged values to the 'Default_Rate' column:
payment_df['Default_Rate'] = merged_df[column_name]


#------------------------------------------------------------------------------
#            ----    Main Code  -  Calculate the columns ----
#------------------------------------------------------------------------------

# Constants
purchase_premium = df['Purchase_Premium'].values[0] / 100
default_multiplier = df['Default_Multiplier'].values[0]
prepay_multiplier = df['Prepay_Multiplier'].values[0]
initial_investment = df['Invested'].values[0]
servicing_rate = df['Servicing_Fee'].values[0]
earnout_fee = df['Earnout_Fee'].values[0]
recovery_rate = df['Recovery_Rate'].values[0]

# Convert non-numeric values to NaN and then the entire column to float
payment_df['Default_Rate'] = payment_df['Default_Rate'].astype(float)

# Before entering the loop, calculate the monthly payment
monthly_payment = npf.pmt(monthly_interest_rate, num_periods, -initial_investment)

zero_columns = [
    'Scheduled_Principal', 'Scheduled_Interest', 'Prepay_Speed', 'Default',
    'Prepay', 'Servicing_CF', 'Recovery', 'Interest_Amount', 'Earnout_CF', 'Principal'
]

for index in range(len(payment_df)):
    # Assign 0 to the first row of the zero collumns
    if index == 0:  # For the first row
        payment_df.loc[index, zero_columns] = 0
        payment_df.at[index, 'Balance'] = initial_investment
        payment_df.at[index, 'Total_CF'] = (- initial_investment * (1 + purchase_premium )).round(2)
        payment_df.at[index, 'Scheduled_Balance'] = initial_investment  # Set the first 'Scheduled_Balance' based on 'Invested'



    else:  # For the rest of the rows

        # Calculate Earnout_CF
        if index in [12, 18]:
           earnout_fee_decimal = earnout_fee  / 100  # Convert from percentage to decimal
           earnout_cf = earnout_fee_decimal / 2 * initial_investment
           payment_df.at[index, 'Earnout_CF'] = earnout_cf

        else:
           earnout_cf = 0
           payment_df.at[index, 'Earnout_CF'] = earnout_cf


        # Calculate Scheduled_Principal for the current row
        #scheduled_principal =  npf.ppmt(monthly_interest_rate, payment_df.at[index, 'Months'] - 1, num_periods, -initial_investment)
        scheduled_principal =  (npf.ppmt(monthly_coupon_rate , payment_df.at[index, 'Months'] - 1, num_periods, -initial_investment)).round(12)
        payment_df.at[index, 'Scheduled_Principal'] = scheduled_principal


        # Calculate Scheduled_Balance
        previous_balance = payment_df.at[index - 1, 'Balance']
        previous_scheduled_balance = payment_df.at[index - 1, 'Scheduled_Balance']
        scheduled_balance = previous_scheduled_balance - scheduled_principal
        # Check if scheduled_balance is less than 0
        if scheduled_balance < 0:
            scheduled_balance = 0
        payment_df.at[index, 'Scheduled_Balance'] = bankers_round(scheduled_balance,12)


        # Calculate Scheduled_Interest
        scheduled_interest = monthly_payment - scheduled_principal
        #print(f"scheduled_interest : {scheduled_interest} = {monthly_payment} - {scheduled_principal}")
        payment_df.at[index, 'Scheduled_Interest'] = scheduled_interest


        # Calculate prepay_speed
        prepay_speed = prepay_df.iloc[index]['36']
        #prepay_speed = pd.to_numeric(prepay_speed, errors='coerce')
        prepay_speed = float(prepay_speed)
        payment_df.at[index, 'Prepay_Speed'] = round(prepay_speed, 4)

        # Calculate Prepay
        prepay = (previous_balance - ((previous_balance - scheduled_interest) / previous_scheduled_balance ) * scheduled_principal ) * prepay_speed * prepay_multiplier
        #print(f"{prepay} = ({previous_balance} - (({previous_balance} - {scheduled_interest}) / {scheduled_balance} ) * {scheduled_principal} ) *{ prepay_speed} * {prepay_multiplier} /100")
        payment_df.at[index, 'Prepay'] = round(prepay, 2)

        # Calculate Default
        previous_default_rate = payment_df.at[index - 1, 'Default_Rate']
        default = previous_balance * previous_default_rate * default_multiplier
        payment_df.at[index, 'Default'] = round(default, 2)

        principal = ((previous_balance - default) / previous_scheduled_balance  * scheduled_principal) + prepay
        #print(f"{principal} = (({previous_balance} - {default}) / {previous_scheduled_balance}  * {scheduled_principal}) + {prepay}")
        payment_df.at[index, 'Principal'] = round(principal, 2)

        # Calculate Balance
        balance = previous_balance - default - principal
        # Check if balance is less than 0
        if balance < 0:
            balance = 0
        payment_df.at[index, 'Balance'] = bankers_round(balance, 16)

        # Calculating servicing cash flow
        servicing_cf = (previous_balance - default) * servicing_rate / 100 / 12
        payment_df.at[index, 'Servicing_CF'] = round(servicing_cf, 2)


        # Calculate Recovery
        recovery = default * recovery_rate
        payment_df.at[index, 'Recovery'] = round(recovery, 2)


        # Calculate Interest_Amount

        interest_amount = (previous_balance - default) * annual_interest_rate / 12
        payment_df.at[index, 'Interest_Amount'] = round(interest_amount, 2)

        # Calculate Total_CF
        total_cf = principal + interest_amount + recovery - servicing_cf - earnout_cf
        payment_df.at[index, 'Total_CF'] = round(total_cf, 2)


#------------------------------------------------------------------------------
#                     ---- IRR &  Print Results   ----
#------------------------------------------------------------------------------

# Calculate the IRR
cash_flows = payment_df['Total_CF'].values
annual_irr = npf.irr(cash_flows) * 12 *100

# Find the longest key length for formatting
max_key_length = max(len(key) for key in data.keys())

# Print header
print(f"{'Parameter':<{max_key_length}} | {'Value'}")

# Print divider
print('-' * (max_key_length + 3 + 10))

payment_df['Default_Rate'] = (payment_df['Default_Rate'] * 100).round(2)


# Print rows
for key, value in data.items():
    print(f"{key:<{max_key_length}} | {value}")

# Print the new DataFrame
print(payment_df)
print()
print("The IRR : ", round_down(annual_irr, 4))

