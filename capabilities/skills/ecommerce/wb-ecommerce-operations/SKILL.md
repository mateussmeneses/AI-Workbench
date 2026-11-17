---
name: wb-ecommerce-operations
description: Use when building or auditing checkout flows, cart/inventory state, pricing/tax rules, payment webhooks, or order fulfillment pipelines.
---

# Ecommerce Operations

## When to apply
- Implementing cart calculations, discount stacking, inventory reservation, or payment gateway webhooks.
- Investigating order state mismatches, double charges, or currency rounding bugs.

## Procedure
1. Use integer minor units (cents) or fixed-precision decimals for all monetary amounts; never use binary floats.
2. Separate quote/cart pricing from immutable order snapshots created at checkout confirmation.
3. Enforce idempotency keys on payment intents and verify webhook cryptographic signatures before updating order status.
4. Guard inventory decrements with atomic DB checks/locks so concurrent checkouts cannot oversell stock.
5. Test refunds, partial captures, expired carts, failed webhooks, and tax/shipping edge cases in sandbox mode.

## Verification
- Order totals equal sum of line items + tax + shipping - discounts to the exact cent.
- Duplicate webhook deliveries are safely ignored without double-fulfilling orders.
