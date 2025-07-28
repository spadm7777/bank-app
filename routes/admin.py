# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Transaction
from datetime import datetime
import math
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/manual_edit', methods=['GET', 'POST'])
@login_required
def manual_edit():
    if current_user.username != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            date = request.form['date']
            username = request.form['user']
            trans_type = request.form['type']
            amount = int(request.form['amount'])
            balance = int(request.form['balance'])
            sender = request.form.get('sender', '(관리자 입력)')

            user = User.query.filter_by(username=username).first()
            if not user:
                flash(f"사용자 '{username}' 를 찾을 수 없습니다.", 'danger')
                return render_template('manual_edit.html')

            fee = math.floor(amount * (user.fee_rate or 0) / 100) if trans_type == '입금' else 0

            new_tx = Transaction(
                user_id=user.id,
                type=trans_type,
                amount=amount,
                balance=balance,
                sender=sender,
                timestamp=datetime.strptime(date, '%Y-%m-%dT%H:%M'),
                fee=fee
            )

            db.session.add(new_tx)
            db.session.commit()

            flash('거래 내역이 성공적으로 추가되었습니다.', 'success')
            return redirect(url_for('index', user_id=user.id))

        except Exception as e:
            db.session.rollback()
            flash(f'오류 발생: {e}', 'danger')

    return render_template('manual_edit.html')


@admin_bp.route('/delete_duplicates', methods=['GET', 'POST'])
@login_required
def delete_duplicates():
    if current_user.username != 'admin':
        flash('접근 권한이 없습니다.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            duplicates = db.session.query(
                Transaction.type,
                Transaction.amount,
                Transaction.balance,
                Transaction.sender,
                func.substr(Transaction.timestamp, 1, 10).label('date'),
                func.count(Transaction.id)
            ).group_by(
                Transaction.type,
                Transaction.amount,
                Transaction.balance,
                Transaction.sender,
                func.substr(Transaction.timestamp, 1, 10)
            ).having(func.count(Transaction.id) > 1).all()

            total_deleted = 0

            for dup in duplicates:
                txs = Transaction.query.filter(
                    Transaction.type == dup[0],
                    Transaction.amount == dup[1],
                    Transaction.balance == dup[2],
                    Transaction.sender == dup[3],
                    Transaction.timestamp.like(f"{dup[4]}%")
                ).order_by(Transaction.timestamp).all()

                for tx in txs[1:]:  # 첫 번째만 남기고 삭제
                    db.session.delete(tx)
                    total_deleted += 1

            db.session.commit()
            flash(f"중복 거래 {total_deleted}건이 삭제되었습니다.", 'success')
        except Exception as e:
            db.session.rollback()
            flash(f"삭제 중 오류 발생: {e}", 'danger')

    return render_template('delete_duplicates.html')
