# Exercise 1: Fake Ping (1%)

## Introduction

In practice, network devices (e.g., firewall, routers) generate ICMP messages like Destination Unreachable, Packet Too Big when there are issues encountered in packet forwarding.
To give you a taste on how this is done, you are asked implement a simple DPDK application that produces ICMP Echo Replies (though they are not exactly error messages, but the idea is similar) in response to ICMP Echo Requests.

[ICMP messages](https://en.wikipedia.org/wiki/Internet_Control_Message_Protocol) are differentiated by their type and code. 
For instance, ICMP Echo Requests are of type 8 and code 0.
To generate an ICMP Echo Reply, the corresponding type and code must be set.
At the same time, the ICMP header checksum needs to be updated accordingly.

### Network Topology

Below is the network topology for this exercise:

```
+-----+         +-----------+
| h1  | <-----> |  switch   |
+-----+         +-----------+
```

- `h1`: The only host in the topology, connected directly to the DPDK software switch.
- `switch`: The DPDK software switch you will implement.

### Requirements

1. The switch shall process ICMP Echo Requests and generate ICMP Echo Replies accordingly.
1. The switch shall respond to ICMP Echo Requests from `h1` to IPs within the `10.0.0.0/8` subnet.
1. The switch shall drop ICMP traffic destined for IPs outside of the `10.0.0.0/8` subnet.

## Step 1: Run the (incomplete) starter code

The directory with this README also contains a skeleton DPDK program, `fake_ping.c`, which currently does nothing. 
Your job will be to extend this skeleton program to implement the required functionality.

Before that, let's compile the incomplete `fake_ping.c` and bring up a switch in Mininet to test its behavior.

1. In your shell, run:
   ```bash
   make run
   ```
   This will:
   * compile `fake_ping.c`, and
   * start the pod-topo in Mininet, and
   * configure all hosts with the commands listed in
   [pod-topo/topology.json](./pod-topo/topology.json)

2. You should now see a Mininet command prompt. 
   Try to ping between any host in the topology:
   ```bash
   mininet> h1 ping 10.0.0.9
   mininet> h1 ping 10.255.255.254
   ```
3. Type `exit` to leave each xterm and the Mininet command line.
   Then, to stop mininet:
   ```bash
   make stop
   ```
   And to delete all pcaps, build files, and logs:
   ```bash
   make clean
   ```

The ping failed because the DPDK software switch currently has incomplete packet processing logic.
Your job is to complete the implementation.

## Step 2: Implement Fake Ping

The `fake_ping.c` file contains a skeleton DPDK program with key pieces of logic replaced by `TODO` comments.
Your implementation should follow the structure given in this file and replace the `TODO`s with logic implementing the missing piece.
You are allowed to add additional functions and include additional DPDK header files as needed, but you should not change the function signatures of the existing functions.

## Step 3: Run your solution

Follow the instructions from Step 1. 
This time, you should be able to sucessfully ping between any IPs from `h1`, except the ones outside of the `10.0.0.0/8` subnet.

### Troubleshooting

There are several problems that might manifest as you develop your program:

1. `fake_ping.c` might fail to compile. 
In this case, `make run` will report the error emitted from the compiler and halt.

2. `fake_ping.c` might compile but `h1` might fail to get any ICMP Echo Responses. 
The `logs/sX.log` files contain detailed logs that describing how each switch processes each packet. 
You can add more logging statements in your code to help you debug the logic.
The output is detailed and can help pinpoint logic errors in your implementation. 
At the same time, you can also take a look at the PCAPs under `pcaps/`.

3. Make sure that the `fake_ping` process is running in the background.
You can check this by running: `ps aux | grep fake_ping`.
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
