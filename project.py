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
import matplotlib.pyplot as plt
import pylab


class Project():
    """This class represents project
    Attributes:
        activities_dict (activity_name : [{next_activity : activity_duration},
            {another_next_activity : anther_next_activity_duration}, ...]

    """
    def __init__(self, activities_dict= None):
        """ initializes a graph object
                   If no dictionary or None is given, an empty dictionary will be used
               """
        if activities_dict == None:
            self.activities_dict = dict()
        else:
            self.activities_dict = activities_dict

    def __str__(self):
        string_to_return = ""
        for activity_node, connected_activities in self.activities_dict:
            string_to_return += '{}: ['.format(activity_node)
            for connected_activity_node, connected_activitiy_duration in connected_activities:
                string_to_return += '{}:{}, '.format(connected_activity_node, connected_activitiy_duration)
            string_to_return += ']\n'
        return string_to_return

    def add_activity(self, activity_name, next_activity=None, activity_duration=None):
        if activity_name in self.activities_dict:
                if dict(next_activity = activity_duration) not in self.activities_dict.get(activity_name):
                    self.activities_dict.get(activity_name).append(dict(next_activity=activity_duration))
        else:
            self.activities_dict.update(activity_name=[dict(next_activity=activity_duration)])



    def remove_activity(self, activity_name):
        if activity_name in self.activities_dict:
            del self.activities_dict[activity_name]
        else:
            print("Can't remove activity that is not in dictionary. Please check your input")


    def validate_project(self):
        G = nx.DiGraph()
        edge_colors = ['black']
        for activity_node, connected_activites_dict in self.activities_dict:
            G.add_node(activity_node)
            for connected_activites_nodes, connected_activites_duration in connected_activites_dict:
                G.add_edges_from([(activity_node, connected_activites_nodes)], weight=connected_activites_duration)

        #define default style for graph
        G.graph['graph'] = {'rankdir': 'TD'}
        G.graph['node'] = {'shape': 'circle'}
        G.graph['edges'] = {'arrowsize': '4.0'}

        pos = nx.lay

        edge_labels = dict([((u, v,), d['weight'])
                            for u, v, d in G.edges(data=True)])

        pos = nx.spring_layout(G)
        nx.draw_networkx_edge_labels(G,pos, edge_labels=edge_labels)
        nx.draw(G, 'black', node_size=1500, edge_color = edge_colors)
        pylab.show()



    def find_isolate_activities(self):
        non_isolated_activities = set()
        for activity_node, connected_activities in self.activities_dict:
            if len(connected_activities) > 0:
                non_isolated_activities.add(activity_node)
            for connected_activity_node, connected_activitiy_duration in connected_activities:
                non_isolated_activities.add(connected_activity_node)
        return  set(self.activities_dict not in non_isolated_activities)



    def find_critical_path(self):
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

    @property
    def activity_duration(self):
        pass