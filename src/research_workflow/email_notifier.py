"""
Email Notification Script - 黒字商品を自動メール送信
"""

import smtplib
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from datetime import datetime

class EmailNotifier:
    def __init__(self, smtp_server: str, smtp_port: int, sender: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.sender = sender
        self.password = password
    
    def send_profit_report(self, recipient: str, report_file: str, csv_file: str):
        """黒字商品レポートをメール送信"""
        
        # レポートを読み込み
        with open(report_file, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        # 黒字案件をフィルタ
        profitable_items = []
        if report.get('samples'):
            profitable_items = [
                item for item in report['samples']
                if item.get('profit_margin_pct', 0) > 0
            ]
        
        # メール本文を作成
        subject = f"📊 MarginScout リサーチレポート - {datetime.now().strftime('%Y-%m-%d')}"
        
        body = f"""
MarginScout v2.0 - リサーチレポート

【実行日時】
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

【サマリ】
- 総入力: {report['summary']['total_inputs']}件
- 出力: {report['summary']['csv_output_count']}件
- 成功率: {report['summary']['success_rate_pct']}%

【黒字案件】
件数: {len(profitable_items)}件

"""
        
        for idx, item in enumerate(profitable_items, 1):
            body += f"""
{idx}. {item.get('product_name', 'N/A')}
   ソース: {item.get('source_channel')}
   利益: ¥{item.get('profit_jpy', 0):,.0f}
   利益率: {item.get('profit_margin_pct', 0):.1f}%
   URL: {item.get('source_url', 'N/A')}

"""
        
        body += f"""
詳細は添付の research_results.csv をご確認ください。

---
MarginScout v2.0
Automated Research Platform
"""
        
        # メール送信
        try:
            msg = MIMEMultipart()
            msg['From'] = self.sender
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            # CSV を添付
            if Path(csv_file).exists():
                with open(csv_file, 'r', encoding='utf-8') as f:
                    csv_content = f.read()
                
                attachment = MIMEText(csv_content, 'plain', 'utf-8')
                attachment.add_header('Content-Disposition', 'attachment', filename='research_results.csv')
                msg.attach(attachment)
            
            # SMTP で送信
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender, self.password)
                server.send_message(msg)
            
            print(f"✅ Email sent to {recipient}")
            
        except Exception as e:
            print(f"❌ Failed to send email: {e}")


# 使用例
if __name__ == "__main__":
    # Gmail の場合
    notifier = EmailNotifier(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        sender="your_email@gmail.com",
        password="your_app_password"  # Gmail アプリパスワード
    )
    
    notifier.send_profit_report(
        recipient="recipient@example.com",
        report_file="output_operational_test/test_report.json",
        csv_file="output_operational_test/research_results.csv"
    )
