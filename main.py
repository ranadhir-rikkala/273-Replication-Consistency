import time

from inventory import Client, Primary, Replica, log


def check(label, ok):
    print(f"    [{'PASS' if ok else 'FAIL'}] {label}", flush=True)


def wait_until(client, name, value, timeout=5.0):
    deadline = time.monotonic() + timeout
    while True:
        current = client.read(name)
        if current == value or time.monotonic() > deadline:
            return current
        time.sleep(0.4)


def main():
    secondary = Replica("secondary", 0)
    primary = Primary(0, secondary, delay=1.0)
    client = Client(primary, secondary)

    print("=== 1. Replication ===", flush=True)
    client.write(10)
    check("primary receives the new value 10", client.read("primary") == 10)
    check("secondary eventually receives 10", wait_until(client, "secondary", 10) == 10)
    check("both replicas return the same value", client.read("primary") == client.read("secondary") == 10)

    print("\n=== 2. Stale read ===", flush=True)
    primary.pause()
    client.write(9)
    check("primary returns 9", client.read("primary") == 9)
    reads = []
    for _ in range(3):
        reads.append(client.read("secondary"))
        time.sleep(0.5)
    log("client", "STALE READ: secondary returns 10 while primary has 9")
    check("secondary temporarily returns the older value 10", reads == [10, 10, 10])

    print("\n=== 3. Recovery and convergence ===", flush=True)
    primary.resume()
    check("secondary eventually updates to 9", wait_until(client, "secondary", 9) == 9)
    check("both replicas return the same value again", client.read("primary") == client.read("secondary") == 9)


if __name__ == "__main__":
    main()
