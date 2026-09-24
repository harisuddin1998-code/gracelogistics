from flask import Blueprint, render_template, request, redirect, url_for, flash, render_template_string, make_response
from models.salary_model import SalaryModel
from models.driver_model import DriverModel
from models.advance_model import AdvanceModel
from datetime import datetime
import pandas as pd
from io import BytesIO
from utils.helpers import form_text_or_none, form_float, form_float_or_none, form_date, form_id

salary_bp = Blueprint('salary', __name__, url_prefix='/salary')


@salary_bp.route('/generate', methods=['GET', 'POST'])
def generate_salary():
    """Generate monthly salary for a driver"""
    if request.method == 'POST':
        month = form_text_or_none(request.form, 'month')
        driver_id = form_id(request.form, 'driver_id')
        driver = DriverModel.get_driver_by_id(driver_id) if driver_id else None
        driver_name = driver['full_name'] if driver and driver['full_name'] else 'driver'
        
        # Check if salary already generated for this driver this month (only when both are given)
        if month and driver_id and SalaryModel.check_salary_generated(month, driver_id):
            flash(f'Salary already generated for {driver_name} for {month}!', 'danger')
            return redirect(url_for('salary.generate_salary'))
        
        # Get pending advance amount for this driver
        pending_advance = AdvanceModel.get_total_pending_by_driver(driver_id) if driver_id else 0
        advance_deduction = form_float_or_none(request.form, 'advance_deduction')
        
        data = {
            'base_salary': form_float(request.form, 'base_salary'),
            'advance_deduction': pending_advance if advance_deduction is None else advance_deduction,
            'bonus': form_float(request.form, 'bonus'),
            'penalty': form_float(request.form, 'penalty'),
            'payment_date': form_date(request.form, 'payment_date'),
            'payment_method': form_text_or_none(request.form, 'payment_method'),
            'generated_by': 1  # Assuming admin user ID 1
        }
        
        # Generate salary record
        salary_id = SalaryModel.generate_salary_month(driver_id, month, data)
        
        # If advance was deducted, mark the pending advance as deducted
        if data['advance_deduction'] > 0 and driver_id:
            # Get all pending advances for this driver
            pending_advances = AdvanceModel.get_advances_by_driver(driver_id)
            for advance in pending_advances:
                if advance['status'] == 'Pending':
                    AdvanceModel.mark_deducted(advance['advance_id'], month)
                    # Update driver's advance balance in drivers table
                    DriverModel.update_advance_balance(driver_id, advance['amount'], 'deduct')
                    break  # Deduct one advance at a time
        
        flash(f'Salary generated successfully for {driver_name}!', 'success')
        return redirect(url_for('salary.print_slip', salary_id=salary_id))
    
    drivers = DriverModel.get_all_drivers()
    current_month = datetime.now().strftime('%Y-%m')
    return render_template('salary/generate.html', drivers=drivers, current_month=current_month)


@salary_bp.route('/print/<int:salary_id>')
def print_slip(salary_id):
    """Print salary slip for a driver"""
    salary = SalaryModel.get_salary_slip(salary_id)
    
    if not salary:
        flash('Salary record not found!', 'danger')
        return redirect(url_for('salary.salary_history'))
    
    # HTML template for salary slip
    slip_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Salary Slip - {{ salary.full_name }}</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f0f2f5;
            }
            .slip-container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
            }
            .company-name {
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 5px;
            }
            .slip-title {
                font-size: 18px;
                opacity: 0.9;
            }
            .content {
                padding: 30px;
            }
            .details {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
            }
            .details table {
                width: 100%;
            }
            .details td {
                padding: 8px;
            }
            .salary-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            .salary-table th, .salary-table td {
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }
            .salary-table th {
                background-color: #f2f2f2;
                font-weight: 600;
            }
            .total {
                font-size: 18px;
                font-weight: bold;
                text-align: right;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 2px solid #eee;
            }
            .footer {
                background: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
                border-top: 1px solid #eee;
            }
            .btn-print {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 10px 20px;
                margin-bottom: 20px;
                border: none;
                border-radius: 8px;
                cursor: pointer;
                font-size: 14px;
            }
            .btn-print:hover {
                background: #5a67d8;
            }
            @media print {
                body {
                    background: white;
                    padding: 0;
                    margin: 0;
                }
                .btn-print {
                    display: none;
                }
                .slip-container {
                    box-shadow: none;
                    border-radius: 0;
                }
            }
        </style>
    </head>
    <body>
        <div style="text-align: center; margin-bottom: 20px;">
            <button class="btn-print" onclick="window.print()">
                <i class="fas fa-print"></i> Print / Save as PDF
            </button>
        </div>
        <div class="slip-container">
            <div class="header">
                <div class="company-name">{{ company_name }}</div>
                <div class="slip-title">MONTHLY SALARY SLIP</div>
            </div>
            
            <div class="content">
                <div class="details">
                    <table>
                        <tr>
                            <td width="50%"><strong>Employee Name:</strong> {{ salary.full_name }}</td>
                            <td><strong>License No:</strong> {{ salary.license_no or 'N/A' }}</td>
                        </tr>
                        <tr>
                            <td><strong>Assigned Vehicle:</strong> {{ salary.assigned_vehicle or 'Not Assigned' }}</td>
                            <td><strong>Month:</strong> {{ salary.month }}</td>
                        </tr>
                        <tr>
                            <td><strong>Payment Date:</strong> {{ salary.payment_date }}</td>
                            <td><strong>Payment Method:</strong> {{ salary.payment_method }}</td>
                        </tr>
                    </table>
                </div>
                
                <table class="salary-table">
                    <thead>
                        <tr><th>Description</th><th>Amount (PKR)</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>Base Salary</td><td>{{ "{:,.2f}".format(salary.base_salary) }}</td></tr>
                        <tr><td>Bonus</td><td class="text-success">+ {{ "{:,.2f}".format(salary.bonus) }}</td></tr>
                        <tr style="color: #dc2626;"><td>Advance Deduction</td><td>- {{ "{:,.2f}".format(salary.advance_deduction) }}</td></tr>
                        <tr style="color: #dc2626;"><td>Penalty</td><td>- {{ "{:,.2f}".format(salary.penalty) }}</td></tr>
                        <tr style="background-color: #f0fdf4; font-weight: bold;">
                            <td><strong>Net Payable</strong>
                            <td><strong>{{ "{:,.2f}".format(salary.net_payable) }} PKR</strong>
                        </tr>
                    </tbody>
                </table>
                
                <div class="total">
                    Amount in Words: {{ words }}
                </div>
            </div>
            
            <div class="footer">
                <p>This is a computer generated salary slip. No signature required.</p>
                <p>Generated on: {{ generated_date }}</p>
            </div>
        </div>
    </body>
    </html>
    '''
    
    # Simple number to words for PKR
    def number_to_words(num):
        if num < 1000:
            return f"{int(num)} Rupees Only"
        elif num < 100000:
            return f"{int(num/1000)} Thousand {int(num%1000)} Rupees Only"
        elif num < 10000000:
            lakhs = int(num / 100000)
            remainder = int(num % 100000)
            if remainder > 0:
                return f"{lakhs} Lakh {int(remainder/1000)} Thousand {remainder%1000} Rupees Only"
            else:
                return f"{lakhs} Lakh Rupees Only"
        else:
            crores = int(num / 10000000)
            remainder = int(num % 10000000)
            if remainder > 0:
                return f"{crores} Crore {int(remainder/100000)} Lakh Rupees Only"
            else:
                return f"{crores} Crore Rupees Only"
    
    # Get company name for display
    from app import app
    company_name = app.config.get('APP_NAME', 'Vehicle Management System')
    
    return render_template_string(slip_html, 
                                 salary=salary, 
                                 words=number_to_words(salary['net_payable']),
                                 generated_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                 company_name=company_name)


@salary_bp.route('/history')
def salary_history():
    """View salary history with filters"""
    month = request.args.get('month')
    driver_id = request.args.get('driver_id', type=int)
    
    records = SalaryModel.get_salary_records(month, driver_id)
    drivers = DriverModel.get_all_drivers()
    
    total_payable = sum(rec['net_payable'] for rec in records)
    
    return render_template('salary/history.html', 
                         records=records, 
                         drivers=drivers, 
                         total_payable=total_payable,
                         selected_month=month, 
                         selected_driver=driver_id)


@salary_bp.route('/bulk-generate', methods=['GET', 'POST'])
def bulk_generate():
    """Generate salaries for all active drivers at once"""
    if request.method == 'POST':
        month = form_text_or_none(request.form, 'month')
        payment_date = form_date(request.form, 'payment_date')
        payment_method = form_text_or_none(request.form, 'payment_method')
        
        # Get all active drivers
        drivers = DriverModel.get_all_drivers()
        active_drivers = [d for d in drivers if d['status'] == 'Active']
        
        generated_count = 0
        skipped_count = 0
        
        for driver in active_drivers:
            driver_id = driver['driver_id']
            
            # Check if salary already generated
            if month and SalaryModel.check_salary_generated(month, driver_id):
                skipped_count += 1
                continue
            
            # Get pending advance
            pending_advance = AdvanceModel.get_total_pending_by_driver(driver_id)
            
            data = {
                'base_salary': float(driver['base_salary'] or 0),
                'advance_deduction': pending_advance,
                'bonus': 0,
                'penalty': 0,
                'payment_date': payment_date,
                'payment_method': payment_method,
                'generated_by': 1
            }
            
            # Generate salary
            salary_id = SalaryModel.generate_salary_month(driver_id, month, data)
            
            # Mark advance as deducted if applicable
            if pending_advance > 0:
                pending_advances = AdvanceModel.get_advances_by_driver(driver_id)
                for advance in pending_advances:
                    if advance['status'] == 'Pending':
                        AdvanceModel.mark_deducted(advance['advance_id'], month)
                        DriverModel.update_advance_balance(driver_id, advance['amount'], 'deduct')
                        break
            
            generated_count += 1
        
        flash(f'Bulk salary generation completed! Generated: {generated_count}, Skipped: {skipped_count}', 'success')
        return redirect(url_for('salary.salary_history'))
    
    current_month = datetime.now().strftime('%Y-%m')
    drivers = DriverModel.get_all_drivers()
    active_count = len([d for d in drivers if d['status'] == 'Active'])
    
    return render_template('salary/bulk_generate.html', 
                         current_month=current_month,
                         active_count=active_count)


@salary_bp.route('/export-excel')
def export_excel():
    """Export salary records to Excel"""
    month = request.args.get('month')
    driver_id = request.args.get('driver_id', type=int)
    
    records = SalaryModel.get_salary_records(month, driver_id)
    
    if not records:
        flash('No salary records found to export!', 'warning')
        return redirect(url_for('salary.salary_history'))
    
    data = []
    for record in records:
        data.append({
            'Driver Name': record['full_name'],
            'Month': record['month'],
            'Base Salary': record['base_salary'],
            'Advance Deduction': record['advance_deduction'],
            'Bonus': record['bonus'],
            'Penalty': record['penalty'],
            'Net Payable': record['net_payable'],
            'Payment Date': record['payment_date'],
            'Payment Method': record['payment_method']
        })
    
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Salary Records', index=False)
    
    output.seek(0)
    filename = f'salary_records_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
    return make_response(
        output.getvalue(),
        200,
        {
            'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'Content-Disposition': f'attachment; filename={filename}'
        }
    )


@salary_bp.route('/delete/<int:salary_id>')
def delete_salary(salary_id):
    """Delete a salary record"""
    result = SalaryModel.delete_salary(salary_id)
    if result:
        flash('Salary record deleted successfully!', 'success')
    else:
        flash('Salary record not found!', 'danger')
    return redirect(url_for('salary.salary_history'))


@salary_bp.route('/api/summary')
def api_summary():
    """Get salary summary for dashboard"""
    from datetime import datetime
    current_month = datetime.now().strftime('%Y-%m')
    
    records = SalaryModel.get_salary_records(current_month)
    total_payable = sum(rec['net_payable'] for rec in records)
    
    return {
        'month': current_month,
        'total_records': len(records),
        'total_payable': total_payable,
        'average_salary': total_payable / len(records) if records else 0
    }