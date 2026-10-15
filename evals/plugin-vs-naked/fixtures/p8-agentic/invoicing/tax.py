RATES = {"CA": 0.0725, "NY": 0.04, "OR": 0.0}


def tax_for(subtotal_cents, region):
    rate = RATES.get(region)
    if rate is None:
        raise KeyError(f"no tax rate for {region}")
    return round(subtotal_cents * rate)
