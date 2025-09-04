# Exercise 3: Learning Switch (2%)

## Introduction

The objective of this exercise is to implement a learning switch using DPDK. 
The learning switch will learn the MAC addresses of connected hosts and forward packets based on the learned addresses.

When the switch receives a packet, it will check if the source MAC address is already in its forwarding table. 
If not, it will record the source MAC address along with the port it was received on. 
For packets destined to a known MAC address, the switch will forward them to the corresponding port. 
If the destination MAC address is unknown, it should drop the packet.
Only flood packets when the destination MAC address is a broadcast address.

### Network Topology

```
    +-------------------+          +-------------------+
    |        h1         |          |        h2         |
    |    10.0.0.1       |          |    10.0.0.2       |
    | 08:00:00:00:01:11 |          | 08:00:00:00:02:22 |
    +-------------------+          +-------------------+
             \                        /
              \                      /
               \                    /
                +------------------+
                |      Switch      |
                +------------------+
               /                    \
              /                      \
    +-------------------+          +-------------------+
    |        h3         |          |        h4         |
    |    10.0.0.3       |          |    10.0.0.4       |
    | 08:00:00:00:03:33 |          | 08:00:00:00:04:44 |
    +-------------------+          +-------------------+
```

The above topology consists of four hosts, `h1`, `h2`, `h3`, and `h4`, which are within the same `10.0.0.0/24` subnet, connected to a DPDK software switch.

### Requirements

1. The switch shall learn the MAC addresses of connected hosts.
2. The switch shall forward packets based on the learned MAC addresses.
3. The switch shall only broadcast packets when the destination MAC address is a broadcast address.

## Step 1: Run the (incomplete) starter code

The directory with this README also contains a skeleton DPDK program, `learning_switch.c`.
Your job will be to extend this skeleton program to implement the learning switch functionality.

Before that, let's compile the incomplete `learning_switch.c` and bring up a switch in Mininet to test its behavior.
1. In your shell, run:
   ```bash
   make run
   ```
   This will:
   * compile `learning_switch.c`, and
   * start the pod-topo in Mininet, and
   * configure all hosts with the commands listed in
   [pod-topo/topology.json](./pod-topo/topology.json)

## Step 2: Implement the Learning Switch Logic

The `learning_switch.c` file contains a skeleton C program with key pieces of logic replaced by `TODO` comments.
Your implementation should follow the structure given in this file and replace the `TODO`s with logic implementing the missing piece.
You are allowed to add additional functions and include additional DPDK header files as needed, but you should not change the function signatures of the existing functions.

## Step 3: Run your solution

After implementing the learning switch logic, you can run your solution by executing:
```bash
make run
```
This will compile your code and start the Mininet instance with the learning switch.
You can then test the functionality by sending packets between the hosts and observing the switch's behavior.

### Troubleshooting

There are several problems that might manifest as you develop your program:

1. `learning_switch.c` might fail to compile. 
In this case, `make run` will report the error emitted from the compiler and halt.

2. `learning_switch.c` might compile but `h1` might fail to get any ICMP Echo Responses. 
The `logs/sX.log` files contain detailed logs that describing how each switch processes each packet. 
You can add more logging statements in your code to help you debug the logic.
The output is detailed and can help pinpoint logic errors in your implementation. 
At the same time, you can also take a look at the PCAPs under `pcaps/`.

3. Make sure that the `learning_switch` process is running in the background.
You can check this by running: `ps aux | grep learning_switch`.
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
