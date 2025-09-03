# Exercise 4: Simple L3 Router (3%)

## Introduction

The objective of this exercise is to implement a simple Layer 3 (L3) router using DPDK. 
The router will forward packets between two hosts located on different subnets.

The router will have three interfaces, each connected to a different subnet.
When a packet arrives at the router, it will determine the appropriate interface to forward the packet based on the destination IP address.
The router will also perform basic packet processing, such as updating the TTL (Time To Live) field and updating the checksum.

### Network Topology 

Below is the network topology used in this exercise:

```
                  +---------+        +-----------+        +-----------+
                  |  h1     |        |  Router   |        |   h2      |
                  |10.0.0.1 |--------|           |--------|192.168.1.1|
                  +---------+   a    |           |   b    +-----------+
                                     |           |
                                     +-----------+
                                           | c
                                           |
                                        +----------+             
                                        |   h3     |             
                                        |172.16.0.1|            
                                        +----------+         

```

| Host | Network | IP Address      | MAC Address         | Default Gateway       |
|------|---------|----------------|---------------------|------------------------|
| h1   | a       | 10.0.0.1/24    | 08:01:00:00:01:11   | 10.0.0.254             |
| h2   | b       | 192.168.1.1/24 | 08:02:00:00:01:11   | 192.168.1.254          |
| h3   | c       | 172.16.0.1/24  | 08:03:00:00:01:11   | 172.16.0.254           |

The router has three interfaces:
- Interface a: connected to subnet a (10.0.0.0/24)
- Interface b: connected to subnet b (192.168.1.0/24)
- Interface c: connected to subnet c (172.16.0.0/24)

All router interfaces have the MAC adddress 88:88:88:88:88:88.

### Requirements

The router shall support the following features:
- Forwarding packets between two hosts on different subnets.
- Updating the TTL field of the IP header.
- Updating the checksum of the IP header.
- Responding to ICMP Echo Requests (ping) with ICMP Echo Replies when destined for the router.


## Step 1: Run the (incomplete) starter code

The directory with this README also contains a skeleton DPDK program, `simple_l3_router.c`, which can only forward packets between the two hosts.
Your job will be to extend this skeleton program to support the L3 routing functionality.

Before that, let's compile the incomplete `simple_l3_router.c` and bring up a switch in Mininet to test its behavior.
1. In your shell, run:
   ```bash
   make run
   ```
   This will:
   * compile `simple_l3_router.c`, and
   * start the pod-topo in Mininet, and
   * configure all hosts with the commands listed in
   [pod-topo/topology.json](./pod-topo/topology.json)


## Step 2: Implement the L3 Router Logic

The `simple_l3_router.c` file contains a skeleton C program with key pieces of logic replaced by `TODO` comments.
Your implementation should follow the structure given in this file and replace the `TODO`s with logic implementing the missing piece.
You are allowed to add additional functions and include additional DPDK header files as needed, but you should not change the function signatures of the existing functions.

## Step 3: Run your solution

After implementing the L3 router logic, you can run your solution by executing:
```bash
make run
```
This will compile your code and start the Mininet instance with the L3 router.
You can then test the functionality by sending packets between the hosts and observing the router's behavior.

### Troubleshooting

There are several problems that might manifest as you develop your program:

1. `simple_l3_router.c` might fail to compile. 
In this case, `make run` will report the error emitted from the compiler and halt.

2. `simple_l3_router.c` might compile but `h1` might fail to get any ICMP Echo Responses. 
The `logs/sX.log` files contain detailed logs that describing how each router processes each packet. 
You can add more logging statements in your code to help you debug the logic.
The output is detailed and can help pinpoint logic errors in your implementation. 
At the same time, you can also take a look at the PCAPs under `pcaps/`.

3. Make sure that the `simple_l3_router` process is running in the background.
You can check this by running: `ps aux | grep simple_l3_router`.
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
