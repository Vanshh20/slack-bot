from slack_sdk.signature import SignatureVerifier
import hashlib
import hmac

# Slack signing secret from .env
SLACK_SIGNING_SECRET = "23b213462aec50b68587ec42c1c294ba"

# Request details from logs for /metrics 3
TIMESTAMP = "1753610085"
REQUEST_BODY = "token=HpVrgu88OXsUKKiPSRSS7wkZ&team_id=T0982A7ADPB&team_domain=testing-jia3852&channel_id=C098AJN2APJ&channel_name=general&user_id=U0982A7AJEM&user_name=vanshnewsbot&command=/metrics&text=3&api_app_id=A097HBYPGLT&is_enterprise_install=false&response_url=https://hooks.slack.com/commands/T0982A7ADPB/9259593097045/O9sreUkxzLi6usN30bELVXYc&trigger_id=9259593142149.9274347353793.6b6c74d673c77fa53187558235990347"
EXPECTED_SIGNATURE = "v0=f5e65df18b9819d0f87e50e22e9e8ded635df20ff64dc88f9d64906f890cc1f5"

def verify_slack_signature(signing_secret, timestamp, body, expected_signature):
    # Create the signature base string
    sig_basestring = f"v0:{timestamp}:{body}"
    
    # Compute the signature
    computed_signature = "v0=" + hmac.new(
        signing_secret.encode('utf-8'),
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    print(f"Computed Signature: {computed_signature}")
    print(f"Expected Signature: {expected_signature}")
    print(f"Match: {computed_signature == expected_signature}")
    
    # Use slack_sdk's SignatureVerifier to validate the EXPECTED signature
    verifier = SignatureVerifier(signing_secret)
    is_valid = verifier.is_valid(body, timestamp, expected_signature)
    print(f"SignatureVerifier Validation (Expected Signature): {is_valid}")

if __name__ == "__main__":
    verify_slack_signature(SLACK_SIGNING_SECRET, TIMESTAMP, REQUEST_BODY, EXPECTED_SIGNATURE)