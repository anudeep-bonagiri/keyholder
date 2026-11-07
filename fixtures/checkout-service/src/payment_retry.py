"""Payment retry path. v2.14.0 (PAY-881) added retry_with_fresh_token."""


def confirm(order, session):
    token = session.payment_token()
    if token is None:
        # v2.14.0: retry with a fresh token instead of failing the order.
        return retry_with_fresh_token(order, session)
    return charge(order, token)


def retry_with_fresh_token(order, session):
    fresh = session.refresh_payment_token()  # returns None for guest checkout
    # BUG: guest sessions have no refreshable token, so `fresh` is None here
    # and the next line raises AttributeError on every guest order.
    return charge(order, fresh.token)


def charge(order, token):
    return {"order": order.id, "token": token, "status": "charged"}
