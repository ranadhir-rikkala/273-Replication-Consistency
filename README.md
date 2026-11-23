# Module 8: Replication & Consistency

For this lab I built a small inventory system in Python with a primary replica, a secondary replica, and a client that can read from either one. The client always writes to the primary. The primary then copies the new value over to the secondary in a background thread, about a second later. I can also pause and resume that copying, which is how I force a stale read.

## Running it

You just need Python 3.9+. There are no packages to install.

```bash
git clone https://github.com/ranadhir-rikkala/273-Replication-Consistency.git
cd 273-Replication-Consistency
python3 main.py
```

The replicas and the client are in `inventory.py`, and `main.py` runs the three tests one after another. I saved the output from my run in [evidence/output.txt](evidence/output.txt).

## Architecture

```
            write                          replicate (async, 1 s delay,
  CLIENT ----------->  PRIMARY  -------------------------------->  SECONDARY
    |                  stock               can be paused)          stock
    |                     ^                                           ^
    +------- read --------+------------------- read ------------------+
```

## Test 1: Replication

Both replicas start at 0. The client sets the stock to 10 on the primary. The primary shows 10 right away, but the secondary keeps saying 0 until the update gets there about a second later. After that both of them return 10.

```
=== 1. Replication ===
[t= 0.00s] client    write primary  stock = 10
[t= 0.00s] primary   stock = 10, queued for secondary
[t= 0.00s] client    read primary   -> stock = 10
    [PASS] primary receives the new value 10
[t= 0.00s] client    read secondary -> stock = 0
[t= 0.41s] client    read secondary -> stock = 0
[t= 0.81s] client    read secondary -> stock = 0
[t= 1.01s] secondary stock = 10 (replicated from primary)
[t= 1.21s] client    read secondary -> stock = 10
    [PASS] secondary eventually receives 10
[t= 1.21s] client    read primary   -> stock = 10
[t= 1.21s] client    read secondary -> stock = 10
    [PASS] both replicas return the same value
```

## Test 2: Stale read

Here I pause replication first, and then change the stock on the primary from 10 to 9. Reading from the primary gives 9. Reading from the secondary still gives 10, even when I keep checking it for a while, because the update never got sent. So anyone reading from the secondary right now gets an old value. That's the stale read.

```
=== 2. Stale read ===
[t= 1.21s] primary   replication to secondary PAUSED
[t= 1.21s] client    write primary  stock = 9
[t= 1.21s] primary   stock = 9, queued for secondary
[t= 1.21s] client    read primary   -> stock = 9
    [PASS] primary returns 9
[t= 1.21s] client    read secondary -> stock = 10
[t= 1.72s] client    read secondary -> stock = 10
[t= 2.22s] client    read secondary -> stock = 10
[t= 2.72s] client    STALE READ: secondary returns 10 while primary has 9
    [PASS] secondary temporarily returns the older value 10
```

## Test 3: Recovery and convergence

Once I resume replication, the update that was waiting on the primary gets sent. The secondary changes to 9, and the two replicas agree again.

```
=== 3. Recovery and convergence ===
[t= 2.72s] primary   replication to secondary RESUMED
[t= 2.72s] client    read secondary -> stock = 10
[t= 3.13s] client    read secondary -> stock = 10
[t= 3.53s] client    read secondary -> stock = 10
[t= 3.73s] secondary stock = 9 (replicated from primary)
[t= 3.94s] client    read secondary -> stock = 9
    [PASS] secondary eventually updates to 9
[t= 3.94s] client    read primary   -> stock = 9
[t= 3.94s] client    read secondary -> stock = 9
    [PASS] both replicas return the same value again
```

## Reflection

Reading from the secondary is quick and takes load off the primary, but the secondary only knows what the primary has already sent it. In my test it kept saying 10 after the primary had already changed to 9. If you want to be sure you see the latest value, you have to read from the primary, or make the primary wait for the secondary to confirm every write. Both of those make things slower and depend more on one machine. For an inventory system I'd read from the primary at checkout, so nobody buys something that's already sold out, and let product pages read from the secondary.
