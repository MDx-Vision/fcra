from flask import Flask, request, jsonify
import os
from datetime import datetime

app = Flask(__name__)

webhook_history = []

@app.route('/')
def home():
    return '''
    <html>
        <head>
            <title>Webhook Receiver</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                h1 { color: #333; }
                .endpoint { background: #f4f4f4; padding: 10px; border-radius: 5px; margin: 20px 0; }
                .history { margin-top: 30px; }
                .webhook-item { background: #fff; border: 1px solid #ddd; padding: 15px; margin: 10px 0; border-radius: 5px; }
                .timestamp { color: #666; font-size: 0.9em; }
                code { background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>🎯 Webhook Receiver</h1>
            <p>Your Flask webhook server is running!</p>
            
            <div class="endpoint">
                <h2>Webhook Endpoint</h2>
                <p>Send POST requests to: <code>/webhook</code></p>
                <p>Example: <code>POST /webhook</code></p>
            </div>
            
            <div class="history">
                <h2>Recent Webhooks (''' + str(len(webhook_history)) + ''')</h2>
                <p><a href="/history">View all webhook history</a></p>
            </div>
        </body>
    </html>
    '''

@app.route('/webhook', methods=['POST', 'GET'])
def webhook():
    if request.method == 'GET':
        return jsonify({
            'message': 'Webhook endpoint is active',
            'method': 'Send POST requests to this endpoint',
            'timestamp': datetime.now().isoformat()
        }), 200
    
    try:
        content_type = request.content_type
        
        if 'application/json' in content_type:
            data = request.get_json()
        else:
            data = {
                'form_data': request.form.to_dict(),
                'args': request.args.to_dict(),
                'data': request.get_data(as_text=True)
            }
        
        headers = dict(request.headers)
        
        webhook_entry = {
            'timestamp': datetime.now().isoformat(),
            'method': request.method,
            'content_type': content_type,
            'headers': headers,
            'data': data,
            'remote_addr': request.remote_addr
        }
        
        webhook_history.append(webhook_entry)
        
        if len(webhook_history) > 100:
            webhook_history.pop(0)
        
        print(f"[WEBHOOK RECEIVED] {datetime.now().isoformat()}")
        print(f"Content-Type: {content_type}")
        print(f"Data: {data}")
        print("-" * 50)
        
        return jsonify({
            'status': 'success',
            'message': 'Webhook received successfully',
            'received_at': webhook_entry['timestamp'],
            'data_received': data
        }), 200
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/history')
def history():
    return jsonify({
        'total_webhooks': len(webhook_history),
        'webhooks': webhook_history
    }), 200

@app.route('/clear', methods=['POST'])
def clear_history():
    webhook_history.clear()
    return jsonify({
        'status': 'success',
        'message': 'Webhook history cleared'
    }), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
