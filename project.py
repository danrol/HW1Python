# class Activity():
#     def __init__(self, next_activities_lst=[], durations_to_next_activities_lst=[]):
#         if next_activities_lst == None:
#             self.next_activities_lst = []
#         else:
#             self.next_activities_lst = next_activities_lst
#
#         if durations_to_next_activities_lst == None and next_activities_lst != None:
#             self.durations_to_next_activities_lst.append(0)
#         elif next_activities_lst == None and next_activities_lst == None:
#             self.durations_to_next_activities_lst = []
#         else:
#             self.durations_to_next_activities_lst = durations_to_next_activities_lst

import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import pylab

class Graph():
    """This class represents project
        Attributes:
        activities_dict (activity_name : [{next_activity : activity_duration},
        {another_next_activity : anther_next_activity_duration}, ...]
    """
    def __init__(self, activities_dict=None):
        """ initializes a graph object
            If no dictionary or None is given, an empty dictionary will be used
        """

        if activities_dict is None:
            self.activities_dict = dict()
        else:
            self.activities_dict = activities_dict

    def __str__(self):
        str_to_print = "\nGraph print:\n"
        str_to_print += "{\n"
        for activity_node, connected_activities in self.activities_dict.items():
            str_to_print += str(activity_node) + ": [ "
            for connected_nodes_dict in connected_activities:
                for next_node, next_node_duration in connected_nodes_dict.items():
                    str_to_print += "{ " + str(next_node) + " : " + str(next_node_duration) + " } "
            str_to_print += "]\n"
        str_to_print += "}"
        return str_to_print

    @property
    def activity_duration(self):
        pass

    def add_activity(self, activity_name, next_activities_lst=[]):
        # if activity_duration is None or activity_duration < 0:
        #      print("Activity duration must be equal or bigger than 0")
        # else:
        if activity_name not in self.activities_dict:
            self.activities_dict.update({activity_name : next_activities_lst})
        else:
            extended_lst = self.activities_dict.get(activity_name)
            extended_lst.extend(next_activities_lst)
            self.activities_dict.update({activity_name : extended_lst})
        #     TODO check for duplicate dictionaries indide list
        print("Added node successfully")

    def remove_activity(self, activity_name):
        #if activity_name in self.activities_dict:
        self.activities_dict.pop(activity_name, "Can't remove activity that is not in dictionary. Please check your input")
        #else:
         #   print("Can't remove activity that is not in dictionary. Please check your input")
        for activity_node, connected_activities in self.activities_dict.items():
            for connected_nodes_dict in connected_activities:
                for connected_activities_node, connected_activities_duration in connected_nodes_dict.items():
                    if activity_name == connected_activities_node:
                        connected_activities.remove(connected_nodes_dict)


    def validate_project(self):
        isolated_activities = self.find_isolate_activities()

        for isolated_activity in isolated_activities:
            self.remove_activity(isolated_activity)

        G = nx.DiGraph()
        edge_colors = ['black']
        for activity_node, connected_activities in self.activities_dict.items():
            G.add_node(activity_node)
            for connected_nodes_dict in connected_activities:
                for connected_activities_nodes, connected_activities_duration in connected_nodes_dict.items():
                     G.add_edges_from([(activity_node, connected_activities_nodes)], weight=connected_activities_duration)

                # for connected_nodes_dict in connected_activities:
                #     for next_node, next_node_duration in connected_nodes_dict.items():
                #         str_to_print += "{ " + str(next_node) + " : " + str(next_node_duration) + " } "

        #define default style for graph
        G.graph['graph'] = {'rankdir': 'TD'}
        G.graph['node'] = {'shape': 'circle'}
        G.graph['edges'] = {'arrowsize': '4.0'}

        pos = nx.spring_layout(G)

        edge_labels = dict([((u, v,), d['weight'])
                            for u, v, d in G.edges(data=True)])

        pos = nx.spring_layout(G)
        nx.draw_networkx_edge_labels(G,pos, edge_labels=edge_labels)
        nx.draw(G, node_color = 'red', node_size=1500, edge_color = 'red')
        pylab.show()
    #     TODO add labeles to graph (inside node's circle)


    def find_isolate_activities(self):
        non_isolated_activities = set()
        isolated_nodes = []
        all_nodes = []
        for activity_node, connected_activities in self.activities_dict.items():
            all_nodes.append(activity_node)
            if len(connected_activities) > 0:
                non_isolated_activities.add(activity_node)
            for connected_nodes_dict in connected_activities:
                for connected_activities_nodes, connected_activities_duration in connected_nodes_dict.items():
                    non_isolated_activities.add(connected_activities_nodes)

        for node in all_nodes:
            if node not in non_isolated_activities:
                isolated_nodes.append(node)
        return isolated_nodes


    def find_critical_path(self):
        pass
        # final_node = len(self.activities_dict)
        # critical_path_duration = 0
        # arrived_to_final_node = False
        # critical_path_edges = set()
        # i = 0
        # tmp_dict = self.activities_dict
        #
        #
        # while arrived_to_final_node == False:
        #
        # for activity_node, connected_activities in tmp_dict:
        #     #if len(connected_activities > 1):
        #     if arrived_to_final_node == False:
        #
        #     while arrived_to_final_node == False:
        #         list(my_dict.keys())[0]
        #
        #     for connected_activity_node, connected_activitiy_duration in connected_activities:
        #         critical_path_duration += connected_activitiy_duration
        #         self.activities_dict.get(connected_activity_node)

    # @property
    # def activity_duration(self):
    #     pass

g = Graph({'start': [{'B': '5 weeks'}, {'C': '7 weeks'}, {'D': '6 weeks'}], 'B': [{'E': '3 weeks'}, {'F': '9 weeks'}],
           'C': [{'E': '1 week'}, {'G': '4 weeks'}], 'D': [{'G': '6 weeks'}, {'F': '13 weeks'}],
           'E': [{'end': '8 weeks'}], 'F': [{'target': '5 weeks'}], 'G': [{'target': '11 weeks'}], 'target': []})
#g.add_activity('E', 'A', 5 )
print(g)

# g.remove_activity('C')
g.add_activity('E', [{'B': 5}, {'C' : 8}])
print(g)

g.add_activity('C', [ {'B' : 90 } ] )
print(g)
# g.validate_project()

g.add_activity('F')
print(g)
g.add_activity('T')
print(g)
print(g)
isolated_nodes = g.find_isolate_activities()
print("\nIsolated nodes:")
for isolated_node in isolated_nodes:
    print(isolated_node)

g.remove_activity('C')
print(g)

g = Graph({'start': [{'B': '5 weeks'}, {'C': '7 weeks'}, {'D': '6 weeks'}], 'B': [{'E': '3 weeks'}, {'F': '9 weeks'}],
           'C': [{'E': '1 week'}, {'G': '4 weeks'}], 'D': [{'G': '6 weeks'}, {'F': '13 weeks'}],
           'E': [{'end': '8 weeks'}], 'F': [{'target': '5 weeks'}], 'G': [{'target': '11 weeks'}], 'target': []})
print (g)






