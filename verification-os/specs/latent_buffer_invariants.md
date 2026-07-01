# Latent buffer invariants (draft)

## INV-1 — Norm bound

Projection operator P satisfies ||P(x)|| <= c * ||x|| for c <= 1.05.

## INV-2 — Associativity on merge

For agent merge operator ⊕: (a ⊕ b) ⊕ c = a ⊕ (b ⊕ c) on shared latent subspace.

## Notes

Upgrade checker from `stub` to Z3 when formal spec stabilizes.
