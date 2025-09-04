# Exercise 2: A Dead Drop Facility (2%)

## Introduction
The objective of this exercise is to implement a dead drop facility to enable secret message exchange through a DPDK software switch.
The dead drop facility has two components: `dead_drop_box` and `dead_drop_box_checksum`, which can hold up to 65536 entries.

When the switch receives a `DROPOFF` message, it will store the message in the designated `dead_drop_box` entry with corresponding `mailboxNum`.
At the same time, the switch computes a CRC32 checksum for the message which will then be stored in corresponding `dead_drop_box_checksum` entry.
Once the `DROPOFF` is successful, it will return a `SUCCESS` message.

On the other hand, when the switch receives a `PICKUP` message, it will retrieve the message from the corresponding `dead_drop_box` entry.
At the same time, the checksum of the retrieved message will be computed and compared against the checksum stored in `dead_drop_box_checksum`.
If the checksum matches, a `SUCCESS` message will be returned, otherwise, a `FAILURE` message will be sent.
Once the message is retrieved from the `dead_drop_box`, the accessed `dead_drop_box` must be "sanitized" and overwritten with the value `0xdeadbeef`.

The switch must first verify that the message is indeed destined for it with the destination IP `10.0.0.254`.
The dead drop facility uses UDP ports `0xFFFF`, and must be accompanied by an 8-byte `SECRET` header with the following format:

```
         0                1                  2              3
  +----------------+----------------+----------------+---------------+
  |             opCode              |            mailboxNum          |
  +----------------+----------------+----------------+---------------+
  |                              message                             |
  +----------------+----------------+----------------+---------------+

```

### Network Topology

Below is the network topology for this exercise:

```
           +---------+           +---------+           +---------+
           |   h1    |-----------|  s1     |-----------|   h2    |
           +---------+           +---------+           +---------+
           10.0.0.1                  10.0.0.254             10.0.0.2
           08:00:00:00:01:11         08:00:00:00:FF:FF       08:00:00:00:02:22
```
The above topology consists of two hosts, `h1` and `h2`, connected to a switch `s1`.
The switch has the IP address `10.0.0.254`.
The hosts `h1` and `h2` have IP addresses `10.0.0.1` and `10.0.0.2`, respectively.

### Requirements

1. For the dead drop facility, the switch shall only process messages destined for the IP address `10.0.0.254` and UDP ports `0xFFFF`.
1. For `DROPOFF`:
   - The switch shall process `DROPOFF` messages and store the message in the designated `dead_drop_box`.
   - The switch shall compute a CRC32 checksum for the message and store it in `dead_drop_box_checksum`.
   - The switch shall return a `SUCCESS` message upon successful `DROPOFF`.
   - If the `dead_drop_box` is already occupied, the switch shall return a `FAILURE` message.
1. For `PICKUP`: 
   - The switch shall process `PICKUP` messages and retrieve the message from the corresponding `dead_drop_box`.
   - The switch shall compute the checksum of the retrieved message and compare it against the checksum stored in `dead_drop_box_checksum`.
   - If the checksum matches, the switch shall return a `SUCCESS` message with the retrieved message.
   - If the checksum does not match, the switch shall return a `FAILURE` message
   - The switch shall sanitize the accessed `dead_drop_box` by overwriting it with the value `0xdeadbeef`.

## Step 1: Run the (incomplete) starter code

The directory with this README also contains a skeleton DPDK program, `dead_drop.c`, which can only forward packet between the two hosts, `h1` and `h2`. 
Your job will be to extend this skeleton program to support the dead drop facility.

Before that, let's compile the incomplete `dead_drop.c` and bring up a switch in Mininet to test its behavior.

1. In your shell, run:
   ```bash
   make run
   ```
   This will:
   * compile `dead_drop.c`, and
   * start the pod-topo in Mininet, and
   * configure all hosts with the commands listed in
   [pod-topo/topology.json](./pod-topo/topology.json)

2. We have implemented two Python-based programs that allows us to deposit and retrieve secret messages from the switch.
You can run the programs directly from the Mininet command prompt:
   ```bash
   mininet> h1 ./message_dropoff.py --mbox 1 --message hi         # use h1 to dropoff message "hi" at mailbox #1
   ... (output omitted)
   Timeout! No message received.
   mininet> h2 ./message_pickup.py --mbox 1                       # use h2 to pickup message at mailbox #1
   ... (output omitted)
   Timeout! No message received.
   ```

3. No message shall be returned by the switch, since the dead drop facility is not implemented. 
Type `exit` to leave each xterm and the Mininet command line.
   Then, to stop mininet:
   ```bash
   make stop
   ```
   And to delete all pcaps, build files, and logs:
   ```bash
   make clean
   ```

Your job is to extend this file to implement the necessary logic to realize the dead drop facility to faciliate secret message exchange.

## Step 2: Enabling Secret Message Exchange

The `dead_drop.c` file contains a skeleton DPDK program with key pieces of logic replaced by `TODO` comments.
Your implementation should follow the structure given in this file and replace the `TODO`s with logic implementing the missing piece.
You are allowed to add additional functions and include additional DPDK header files as needed, but you should not change the function signatures of the existing functions.

## Step 3: Run your solution

### Normal Case 

Follow the instructions from Step 1. 
This time, you should be able to sucessfully dropoff a message using `h1` and retrieve the corresponding message using `h2`.

### Tampered Case

In addition, you should also make sure that if the secret message is tampered with, the switch should return with a `FAILURE` message after comparing the checksums. 

To allow you to test this, we provide a tool, `secret_util` under `secret_util/` for you to directly read/ modify the secret message in the switch.
If the executable is not built, you can build it by running `make && chmod +x secret_util` in the `secret_util/` directory.

Usage:
```bash
# to read the message at mailbox <mailboxNum>
$ sudo ./secret_util/secret_util read <mailboxNum>

# to write a message at mailbox <mailboxNum>
$ sudo ./secret_util/secret_util write <mailboxNum> <message>
```

### Troubleshooting

There are several problems that might manifest as you develop your program:

1. `dead_drop.c` might fail to compile. 
In this case, `make run` will report the error emitted from the compiler and halt.

2. `dead_drop.c` might compile but `h1` might fail to get any ICMP Echo Responses. 
The `logs/sX.log` files contain detailed logs that describing how each switch processes each packet. 
You can add more logging statements in your code to help you debug the logic.
The output is detailed and can help pinpoint logic errors in your implementation. 
At the same time, you can also take a look at the PCAPs under `pcaps/`.

3. Make sure that the `dead_drop` process is running in the background.
You can check this by running: `ps aux | grep dead_drop`.
If you do not see the process, it means that the DPDK software switch may have exited unexpectedly.
If this is the case, you can check the `logs/sX.log` files for any error messages that may have caused the exit.
Alternatively, make sure that you do not have any `return` statements in the main loop of your program, as this will cause the program to exit prematurely.

#### Cleaning up Mininet

In the latter two cases above, `make run` may leave a Mininet instance running in the background. 
Use the following command to clean up these instances:

```bash
make stop
```

## Running the Packet Test Framework (PTF)

We will be grading your using the Packet Test Framework (PTF), which allows us to specify test cases with different input/output packets to verify your DPDK data plane program behavior.
This is inline with modern software engineering practices.

We have provided some public test cases that you can use to quickly test your program.
For that, simply do `./runptf.sh`.

Note that passing all the public test cases do not necessarily mean that you will get full marks for the exercise as there are other hidden test cases that will be used during grading.
In addition, not all public test cases will be scored as some are purely for sanity check.
