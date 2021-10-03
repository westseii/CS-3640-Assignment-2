"""
cs3640-a2-p1.py | UIowa CS3640 | Fall 2021

Assignment 2 programming component:
Studying link layer characteristics with the Mininet network emulator
[50 points]
-----------------------------------------------


In this assignment, you will learn how to use Mininet to emulate a local network and measure the performance
characteristics of the network.

Important: Read the comments in the function descriptions to understand what needs to be implemented. You may **not**
           use any additional packages beyond the ones imported here. All code will be tested using Python3.

           There are checkpoints along the way which you may use in conjunction with the Tests class to test your code.
           There are 7 checkpoints! Please scroll past the Test class to find the 7th.

References that will be useful for completion of this assignment:
    - What is Mininet: https://github.com/mininet/mininet/wiki/Introduction-to-Mininet#what
    - Installing Mininet: http://mininet.org/download/ (for easiest install: I recommend using Option 2 or 3)
        - for option 2, make sure to install using the '-a' flag.
        - for option 3, make sure to install/start the openvswitch-switch service
    - Getting started with Mininet as a CLI tool: https://github.com/mininet/mininet/wiki/Documentation
    - Mininet's Python API: http://mininet.org/api/hierarchy.html
    - Examples of Mininet scripts: https://github.com/mininet/mininet/tree/master/examples

Evaluation:
    - Your code will be evaluated against a variety of test topologies.
    - Each function that is correctly implemented to handle our test topologies will receive full points.
        - Partial credit will be awarded (rarely) at the instructor's discretion.

Submission:
    - You are required to submit:
            (1) this completed script,
            (2) a README.md file which contains your group members names and a credit reel,
            (3) a link to a PRIVATE github repository which shows your commit history.
    - 5 points will be awarded for correctly following the submission requirements.

"""

import os
import json
import random

import re

from mininet.net import Mininet
from mininet.topo import Topo
from mininet.link import TCLink
from mininet.log import setLogLevel

# setLogLevel('debug')

from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree as mst

import matplotlib.pyplot as plt

# my commit


class EmulateNet:
    """
    Class for functions to handle Mininet topology construction, starting/stopping of the emulator.
    """

    def __init__(self, topology_dict):
        """
        :param topology_dict: This is a dictionary containing information about the topology of the network to
                              be emulated. It contains a list of hosts, a list of switches, and a list of links.
                              topology_dict_noloops.json is a JSON file which demonstrates the format required.
                              topology_dict_loops.json is a JSON file which contains a topology with loops.
        """
        self.hosts, self.switches = [], []
        self.links = []
        self.minimum_spanning_tree = (
            None  # This is a matrix that holds the MST of the network.
        )
        self.topology = None
        self.__create_net_from_topology_dict(topology_dict)
        self.emulated_net = Mininet(
            topo=self.topology, link=TCLink
        )  # We use the TCLink link object because we'd
        # like to be able to have control over link characteristics such as bandwidth, loss, etc.

    def __create_net_from_topology_dict(self, topology_dict):
        """
        Checkpoint ID: 1
        Max score: 10 points

        This function takes a topology_dict dictionary and constructs a Topo() object which reflects the hosts,
        switches, and links described in the dictionary. If loops are found in the topology_dict, they should be
        removed in the constructed topology. The loop-free Topo() object is stored in `self.topology'.

        This method also sets the self.hosts, self.switches, self.links, and self.minimum_spanning_tree variables
        based on the provided topology.

        :param topology_dict: Dictionary containing topology of network to be emulated.
        :return:
        """

        #
        # go
        self.topology = Topo()

        #
        # !!! CREATE CSR FROM TOPO FILE
        # !!! CREATE MST FROM CSR
        # !!! CREATE TOPO FROM MST
        # eliminate loops - mst

        """
        relative paths
        ./topology_dict_noloops.json
        ./topology_dict_loops.json
        """

        # !!! OVERRIDING FOR NOLOOPS
        with open("./topology_dict_noloops.json") as f:
            dict = json.load(f)

        self.hosts = dict["hosts"]
        self.switches = dict["switches"]
        self.links = dict["link_params"]

        for host in self.hosts:
            # str name
            self.topology.addHost(host)
        for switch in self.switches:
            # str name
            self.topology.addSwitch(switch)
            # dict {}
        for link in self.links:
            self.topology.addLink(
                link["source"], link["destination"], **link["options"]
            )

    def show_topology_characteristics(self):
        """
        Helper function that shows you the topology of your constructed network. Use this to verify the correctness of
        your constructed topology.
        """
        print("Hosts in constructed topology:", self.topology.hosts(sort=True))
        print("Switches in constructed topology:", self.topology.switches(sort=True))
        print("Links in constructed topology:\n")
        for link in self.topology.links(sort=True, withInfo=True, withKeys=True):
            print(link)

    def start_emulator(self):
        """
        Checkpoint ID: 2
        Max score: 2.5 points

        Start Mininet emulation of constructed network
        :return:
        """

        self.emulated_net.start()

    def stop_emulator(self):
        """
        Checkpoint ID: 3
        Max score: 2.5 points

        Stop Mininet emulation
        :return:
        """

        self.emulated_net.stop()


class AnalyzePerformanceCharacteristics:
    """
    Class for functions that test an emulated network's reachability and performance.
    """

    def __init__(self, em_net):
        """
        :param em_net: This is an EmulateNet object.
        """
        self.em_net = em_net

    def run_pings(self, hosts=None, timeout="0.01"):
        """
        Checkpoint ID: 4
        Max score: 5 points

        Runs a ping between each host in `hosts'.
        If `hosts' is None, it runs a ping between all pairs of hosts.
        Keep in mind that network emulation should have started before pings can be executed.

        :param hosts: A list of host names or None.
        :param timeout: The maximum time to wait for a ping response.
        :return: p_loss: The fraction of pings that did not complete.
        """

        # do I need this?
        self.em_net.emulated_net.waitConnected()

        p_loss = 0

        #
        # run pings
        if hosts == None:
            p_loss = self.em_net.emulated_net.pingAll(timeout)
        else:
            hostNodes = []
            for host in hosts:
                hostNodes.append(self.em_net.emulated_net.get(host))
            p_loss = self.em_net.emulated_net.ping(hostNodes, timeout)

        return p_loss

    def run_iperf(self, client, server, l4Type="UDP", udpBw="1M", seconds=3):
        """
        Checkpoint ID:5
        Max score: 5 points

        Runs the iperf program to generate traffic from the client to server host.
        Traffic characteristics are specified are function arguments.

        Note that the client speed refers to the sending rate.
        See: http://mininet.org/api/classmininet_1_1net_1_1Mininet.html#a8e07931f87a08d793bdaefbfa5c279e7

        :param client: The client host name
        :param server: The server host name
        :param l4Type: Transport layer to be used. We will only work with UDP in this assignment.
        :param udpBw: Bandwidth of traffic for a client to generate.
        :param seconds: Time in seconds for traffic to be generated.
        :return: Receiving rate (throughput) at server in MBps
        """

        #
        # run iPerf between two nodes
        speeds = self.em_net.emulated_net.iperf(
            [
                self.em_net.emulated_net.get(client),
                self.em_net.emulated_net.get(server),
            ],
            l4Type,
            udpBw,
            seconds,
        )

        print(speeds)

        rec = re.findall(r"\d*\.\d+|\d+", speeds[1])  # 1 == server?

        return float(rec[0])

    def get_average_throughput_all_pairs(self, iterations=2, udpBw="1M", seconds=3):
        """
        Checkpoint ID: 6
        Max score: 5 points

        Runs iperf between all pairs of hosts in the network for 'seconds' sec.
        Pairs are not run simultaneously.
        This is repeated 'iterations' times.
        Returns the average server receiving rate observed in the network.

        :param iterations: The number of iterations over which the average is computed.
        :param udpBw: Bandwidth of UDP traffic generated by each client.
        :param seconds: The time in seconds for the traffic to be generated.
        :return: Average server receiving rate (in MBps) over all pairs and all iterations.
        """


class Tests:
    """
    Collection of functions to help you test your own code.

    Note: There are no guarantees of the completeness of the tests here. In fact, I guarantee that this is incomplete.
    These are just helper functions to help you identify bugs in your own code.
    I expect you to do more extensive testing.
    """

    def __init__(self, checkpoint=0):
        """
        :param checkpoint: The ID of the checkpoint until which you'd like your code to be tested.
        """
        self.em_net = None
        self.a_perf = None
        self.topology_configs = [
            "./topology_dict_loops.json",
            "./topology_dict_noloops.json",
        ]
        if checkpoint == 1:
            self.__run_cp1()
        elif checkpoint == 2:
            self.__run_cp2()
        elif checkpoint == 3:
            self.__run_cp3()
        elif checkpoint == 4:
            self.__run_cp4()
        elif checkpoint == 5:
            self.__run_cp5()
        elif checkpoint == 6:
            self.__run_cp6()
        elif checkpoint == 7:
            self.__run_cp7()
        elif checkpoint > 7:
            print("Invalid checkpoint ID. (valid IDs: 0 to 7)")

    def __run_cp1(self):
        os.system("sudo mn -c")
        filename = self.topology_configs[
            random.randint(1, len(self.topology_configs)) - 1
        ]
        print("Constructing topology from %s" % filename)
        with open(filename) as fp:
            topology_dict = json.load(fp)
        self.em_net = EmulateNet(topology_dict)
        self.em_net.show_topology_characteristics()
        print(
            "Checkpoint 1 reached [10 points]. Inspect your constructed network to verify correctness with "
            "specifications. Is it loop free? Do the links have the same characteristics as in the input?"
        )

    def __run_cp2(self):
        self.__run_cp1()
        self.em_net.start_emulator()
        print(
            "Checkpoint 2 reached [12.5 points]. Did Mininet begin emulating your network as expected?"
        )

    def __run_cp3(self):
        self.__run_cp2()
        self.em_net.stop_emulator()
        print(
            "Checkpoint 3 reached [15 points]. Did Mininet stop emulating your network as expected?"
        )

    def __run_cp4(self):
        self.__run_cp1()
        self.em_net.start_emulator()
        self.a_perf = AnalyzePerformanceCharacteristics(self.em_net)
        host_ids = []
        p_loss = self.a_perf.run_pings()
        print("Packet loss rate during pings [all pairs]: %10.2f" % p_loss)
        while len(host_ids) < 2:
            host_ids = list(
                set(
                    [
                        random.randint(1, len(self.em_net.hosts)) - 1
                        for i in range(0, random.randint(1, len(self.em_net.hosts)) - 1)
                    ]
                )
            )
        p_loss = self.a_perf.run_pings([self.em_net.hosts[i] for i in host_ids])
        print("Packet loss rate during pings [random pairs]: %10.2f" % p_loss)
        self.em_net.stop_emulator()
        print(
            "Checkpoint 4 reached [20 points]. Did the pings run error free? Is the packet loss rate accurate?"
        )

    def __run_cp5(self):
        self.__run_cp1()
        self.em_net.start_emulator()
        self.a_perf = AnalyzePerformanceCharacteristics(self.em_net)
        host_ids = []
        while len(host_ids) < 2:
            host_ids = list(
                set([random.randint(1, len(self.em_net.hosts)) - 1 for i in range(2)])
            )
            hosts = [self.em_net.hosts[i] for i in host_ids]
        receiving_rate = self.a_perf.run_iperf(
            hosts[0], hosts[1], udpBw="10M", seconds=2
        )
        print("Receiving rate: %10.2f" % receiving_rate)
        self.em_net.stop_emulator()
        print(
            "Checkpoint 5 reached [25 points]. Did the iperf run error free? Does the receiving rate match the "
            "output of the iperf program on your console? Are the units as you expected?"
        )

    def __run_cp6(self):
        self.__run_cp1()
        self.em_net.start_emulator()
        self.a_perf = AnalyzePerformanceCharacteristics(self.em_net)
        avg_receiving_rate = self.a_perf.get_average_throughput_all_pairs(
            iterations=3, udpBw="1M", seconds=2
        )
        print("Average receiving rate across all pairs: %10.2f" % avg_receiving_rate)
        self.em_net.stop_emulator()
        print(
            "Checkpoint 6 reached [30 points]. Did the iperf run error free? Does the average "
            "receiving rate match the output of the iperf program on your console? Did all pairs of hosts test "
            "iperf?"
        )

    @staticmethod
    def __run_cp7():
        plot_impact_of_link_characteristics()
        print(
            "Checkpoint 7 reached [45 points]. Did the plots generate successfully? Have you properly "
            "converted all your units? Do the results make sense? "
            "What is your understanding of what the plots are demonstrating?"
        )

    @staticmethod
    def plot_xy(x, y, x_label, y_label, filename):
        """
        Generates a x vs. y plot that is saved in filename.

        :param x: A list of x values
        :param y: A list of y values
        :param x_label: The label for the x axis
        :param y_label: The label for the y axis
        :param filename: The filename that will contain the generated graph
        :return:
        """
        plt.figure()
        plt.title(x_label + " vs. " + y_label)
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.plot(x, y)
        plt.savefig(filename)

    def generate_topology_dicts(
        self, test_param="transmission_rate", topology_vector=None
    ):
        """
        Generates a dictionary of topology dictionaries generated based on the topology specified in 'topology_vector'
        that modify the 'test_param' link options.

        :param test_param: 'transmission_rate', 'loss_rate', or 'queue_size'.
                           'transmission_rate' generates 4 topology dictionaries, each with a different link transmission rate.
                           'loss_rate' generates 4 topology dictionaries, each with a different average link loss rate.
                           'queue_size' generates 3 topology dictionaries, each with a different link buffer size.
        :param topology_vector: A list indicating the number of hosts connected to the ith switch. For example:
                                                                h10
                                                                 |
                                [1, 2, 1] indicates: h00---s0---s1---s2---h20
                                                                 |
                                                                h11
        :return:
        """
        if topology_vector is None:
            topology_vector = [
                random.randint(1, 4) for i in range(random.randint(2, 4))
            ]
        topologies = {}
        if test_param == "transmission_rate":
            for bw in [1000, 100, 10, 5]:
                link_options = {"bw": bw, "loss": 0, "max_queue_size": 10 ** 5}
                topologies["bw=%d" % bw] = self.create_topology_dict_with_options(
                    topology_vector, link_options
                )
        if test_param == "loss_rate":
            for loss in [1, 10, 20, 30]:
                link_options = {"bw": 1000, "loss": loss, "max_queue_size": 10 ** 5}
                topologies["loss=%d" % loss] = self.create_topology_dict_with_options(
                    topology_vector, link_options
                )
        if test_param == "queue_size":
            for q_size in [10 ** 2, 10 ** 1, 1]:
                link_options = {"bw": 1000, "loss": 0, "max_queue_size": q_size}
                topologies[
                    "q_size=%d" % q_size
                ] = self.create_topology_dict_with_options(
                    topology_vector, link_options
                )
        return topologies

    @staticmethod
    def create_topology_dict_with_options(topology_vector, link_options):
        d = {
            "switches": ["s%d" % i for i in range(0, len(topology_vector))],
            "hosts": sum(
                [
                    ["h%d%d" % (i, j) for j in range(0, topology_vector[i])]
                    for i in range(0, len(topology_vector))
                ],
                [],
            ),
            "link_params": [],
        }
        for s_no in range(len(topology_vector)):
            if s_no < len(topology_vector) - 1:
                d["link_params"].append(
                    {
                        "source": "s%d" % s_no,
                        "destination": "s%d" % (s_no + 1),
                        "options": link_options,
                    }
                )
            for h_no in range(topology_vector[s_no]):
                d["link_params"].append(
                    {
                        "source": "h%d%d" % (s_no, h_no),
                        "destination": "s%d" % s_no,
                        "options": link_options,
                    }
                )
        return d


def plot_impact_of_link_characteristics():
    """
    Checkpoint ID: 7
    Max score: 15 points

    Using the helper functions Tests.generate_topology_dicts() and Tests.plot_xy(), generate three graphs that
    illustrate the impact of modifying link transmission rates, link loss rates, and queue size on the average
    server receiving rate in a network.

    Note: You will want the udpBw to generally be high --- around 100MBps+

    :return:
    """


def main():
    """
    Use the main function as you see fit.
    :return:
    """
    os.system(
        "sudo mn -c"
    )  # This will clear up any residue from previous Mininet runs that might
    # interfere with your current run.
    Tests(checkpoint=4)


if __name__ == "__main__":
    main()
