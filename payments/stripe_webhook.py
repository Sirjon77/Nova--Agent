
import os
import stripe
import logging
from flask import Flask, request, abort

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route('/stripe/webhook', methods=['POST'])
def stripe_webhook():
    sig_header = request.headers.get('Stripe-Signature')
    try:
        event = stripe.Webhook.construct_event(
            request.data, sig_header, endpoint_secret
        )
    except ValueError:
        logger.warning('Invalid payload')
        abort(400)
    except stripe.error.SignatureVerificationError:
        logger.error('Invalid signature')
        abort(400)
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout(session)
    return '', 200

def handle_checkout(session):
    # TODO: insert into double‑entry ledger and link to content funnel
    pass

if __name__ == '__main__':
    app.run(port=4242)
