# Compact Source Review Map

The compact contract source is optimized for GenVM source-size constraints.
This file provides the reviewer-facing meaning of the shortest persisted fields.

## Authorization `RequestRecord`

| Compact | Meaning |
|---|---|
| `a` | state |
| `b` | agent |
| `c` | mandate ID |
| `d` | mandate version |
| `e` | mandate commitment |
| `f` | action type |
| `g` | action type hash |
| `h` | target |
| `i` | target commitment |
| `j` | recipient |
| `k` | recipient commitment |
| `l` | value |
| `m` | payload |
| `n` | payload hash |
| `o` | authorized consumer |
| `p` | nonce |
| `q` | issued at |
| `r` | expires at |
| `s` | action subject |
| `t` | request ID |
| `u` | evidence count |
| `v` | evidence-set commitment |
| `w` | action intent |
| `x` | evidence revision |
| `y` | repair reason |
| `z` | repair deadline |
| `aa` | human approved |
| `ab` | human approver |
| `ac` | human approved at |
| `ad` | receipt ID |
| `ae` | receipt consumed |

## Authorization `MandatePolicy`

| Compact | Meaning |
|---|---|
| `a` | max value |
| `b` | max request lifetime |
| `c` | repair window |
| `d` | allowed action hashes |
| `e` | allowed target commitments |
| `f` | allowed recipient commitments |
| `g` | required primary count |
| `h` | required corroboration count |
| `i` | max publication age |
| `j` | max observation age |
| `k` | max publish/observe gap |
| `l` | max evidence records |
| `m` | max evidence body bytes |
| `n` | semantic criteria |
| `o` | authority role masks |
| `p` | authority IDs |
| `q` | authority publisher names |
| `r` | authority source prefixes |
| `s` | authority rule hashes |
| `t` | human mode |
| `u` | human approver |

The public method names remain descriptive. This map is documentation only and
must never be used as a substitute for exact source hashes, ABI/schema output,
or full-runtime source-parity verification.
