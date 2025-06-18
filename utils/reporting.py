import pandas as pd
from io import BytesIO
from models.financial import Contribution, Loan

def generate_member_statement(member_id):
    # Get data
    contributions = Contribution.query.filter_by(member_id=member_id).all()
    loans = Loan.query.filter_by(member_id=member_id).all()
    
    # Create DataFrames
    contrib_df = pd.DataFrame([{
        'Date': c.date,
        'Amount': c.amount,
        'Type': 'Contribution'
    } for c in contributions])
    
    loans_df = pd.DataFrame([{
        'Date': l.date_issued,
        'Amount': l.amount,
        'Type': 'Loan'
    } for l in loans])
    
    # Combine and process
    combined = pd.concat([contrib_df, loans_df])
    summary = combined.groupby('Type').agg({'Amount': ['count', 'sum']})
    
    # Generate Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        combined.to_excel(writer, sheet_name='Transactions')
        summary.to_excel(writer, sheet_name='Summary')
    
    return output.getvalue()