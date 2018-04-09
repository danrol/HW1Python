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

    def __init__(self, activities_dict=None, essential_activities=None):
        """ initializes a graph object
            If no dictionary or None is given, an empty dictionary will be used
        """

        if activities_dict is None:
            self.activities_dict = dict()
        else:
            self.activities_dict = activities_dict

        self._essential_activities = essential_activities

        self._es_ls_ef_lf = dict()
        # TODO define default 0 for every value (4 values at all) in self._es_ls_ef_lf lists
        for activity_node, next_activities in self.activities_dict.items():
            self._es_ls_ef_lf[activity_node] = [0] * 4

        self._project_duration = 0

    def print_essential_activities(self):
        print("\nEssential activities: ")
        str_builder = "{ "
        for activity, essential_activities_lst in self._essential_activities.items():
            str_builder += "'" + activity + "'" + " : [ "
            for essential_activity in essential_activities_lst:
                str_builder += "'" + essential_activity + "' "
            str_builder += "] "
        str_builder += "}"
        print(str_builder)

    @property
    def essential_activities(self):
        return self._essential_activities

    @essential_activities.setter
    def essential_activities(self, essential_activities=None):
        if essential_activities is None:
            self.essential_activities = dict()
        else:
            self._essential_activities = essential_activities

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
    def project_duration(self):
        return int(self._project_duration)

    @project_duration.setter
    def project_duration(self, project_duration):
        self._project_duration = project_duration

    def add_activity(self, activity_name, next_activities_lst=[]):
        # if activity_duration is None or activity_duration < 0:
        #      print("Activity duration must be equal or bigger than 0")
        # else:
        if activity_name != 'end':
            if activity_name not in self.activities_dict:
                self.activities_dict.update({activity_name: next_activities_lst})
            else:
                extended_lst = self.activities_dict.get(activity_name)
                extended_lst.extend(next_activities_lst)
                self.activities_dict.update({activity_name: extended_lst})
            #       TODO check for duplicate dictionaries inside list
            print("Added node successfully")

    def remove_activity(self, activity_name):
        '''try to remove activity if activity not in dictionary, print:
         "Can't remove activity that is not in dictionary. Please check your input'''
        self.activities_dict.pop(activity_name,
                                 "Can't remove activity that is not in dictionary. Please check your input")

        for activity_node, connected_activities in self.activities_dict.items():
            for connected_nodes_dict in connected_activities:
                for connected_activities_node, connected_activities_duration in connected_nodes_dict.items():
                    if activity_name == connected_activities_node:
                        connected_activities.remove(connected_nodes_dict)

    def find_and_remove_isolate_activities(self):
        isolated_activities = self.find_isolate_activities()

        for isolated_activity in isolated_activities:
            self.remove_activity(isolated_activity)

    def validate_project(self):
        self.find_and_remove_isolate_activities()
        print("\n All circles:")
        print(self.find_all_circles())

        # G = nx.DiGraph()
        # edge_colors = ['black']
        # for activity_node, connected_activities in self.activities_dict.items():
        #     G.add_node(activity_node)
        #     for connected_nodes_dict in connected_activities:
        #         for connected_activities_nodes, connected_activities_duration in connected_nodes_dict.items():
        #              G.add_edges_from([(activity_node, connected_activities_nodes)],
        #                               weight=connected_activities_duration)

        # define default style for graph
        # G.graph['graph'] = {'rankdir': 'TD'}
        # G.graph['node'] = {'shape': 'circle'}
        # G.graph['edges'] = {'arrowsize': '4.0'}
        #
        # pos = nx.spring_layout(G)
        #
        # edge_labels = dict([((u, v,), d['weight'])
        #                     for u, v, d in G.edges(data=True)])
        #
        # pos = nx.spring_layout(G)
        # nx.draw_networkx_edge_labels(G,pos, edge_labels=edge_labels)
        # nx.draw(G, node_color = 'red', node_size=1500, edge_color = 'red')
        # pylab.show()

    #     TODO add labeles to graph (inside node's circle)

    def find_all_circles_helper(self, start_node, end_node):
        fringe = [(start_node, [])]
        while fringe:
            state, path = fringe.pop()
            if path and state == end_node:
                yield path
                continue
            for next_dicts in self.activities_dict[state]:
                for next_state, next_state_duration in next_dicts.items():
                    if next_state in path:
                        continue
                    fringe.append((next_state, path + [next_state]))

    def find_all_circles(self):
        circles = [[node] + path for node in self.activities_dict for path in self.find_all_circles_helper(node, node)]
        return circles

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

    def find_all_paths(self, start_vertex='start', end_vertex='end', path=[]):
        """ find all paths from start_vertex to
            end_vertex in graph """
        graph = self.activities_dict
        path = path + [start_vertex]
        if start_vertex == end_vertex:
            return [path]
        if start_vertex not in graph.keys():
            return []
        paths = []
        for next_nodes_dict in graph[start_vertex]:
            for vertex in next_nodes_dict.keys():
                if vertex not in path:
                    extended_paths = self.find_all_paths(vertex, end_vertex, path)
                    for p in extended_paths:
                        paths.append(p)
        return paths

    # def fill_essential_nodes_es_ls(self, start_node = 'start', end_node = 'end'):
    #     all_paths = self.find_all_paths(start_node, end_node)
    #     for activity, essential_nodes_lst in self.essential_activities.items():
    #         for essential_node in essential_nodes_lst:
    #             for index, path in enumerate(all_paths):
    #                 if essential_node in path:
    #                     for node_index, node in enumerate(path):
    #                         for dicts in self.activities_dict[node]:
    #                             for next_node, next_node_duration in dicts.items():
    #                                 es_for_essential_node = 0
    #                                 if next_node == path[node_index+1]:
    #                                     es_for_essential_node += next_node_duration
    #                                 if next_node == essential_node:
    #                                     essential_node_duration = next_node_duration
    #                                     break
    #                                 needed_list = [0]*4
    #                                 old_es_list = self._es_ls_ef_lf.get(essential_node)
    #                                 old_es = old_es_list[0]
    #                                 max_essential_duration = max(old_es, es_for_essential_node)
    #                                 needed_list[0] = max_essential_duration
    #                                  # needed_list[1] = needed_list[0]+essential_node_duration
    #                                 needed_list[2] = self._es_ls_ef_lf[essential_node][2]
    #                                 needed_list[3] = self._es_ls_ef_lf[essential_node][3]
    #                                 self._es_ls_ef_lf[essential_node] = needed_list

    # def check_essentials(self, node, duration = 0):
    #     if node not in self.essential_activities:
    #         return
    #     for essential_node in self.essential_activities[node]:
    #         if essential_node in self.essential_activities:
    #            return self.check_essentials(essential_node) + self.check_how_much_time_until_essential_finished(essential_node)
    #
    #
    # def find_es_ls_ef_lf(self, start_node = 'start', end_node = 'end'):
    #     paths = self.find_all_paths(start_node, end_node)
    #     for paths_lst_index, path_list in enumerate(paths):
    #         for single_path_index, node in enumerate(path_list):
    #             if node != end_node:
    #                 next_nodes_list = self.activities_dict.get(node)
    #                 for next_node_dict in next_nodes_list:
    #                     next_node_to_find = path_list[single_path_index + 1]
    #                     self.check_essentials(node)

    def find_critical_path(self, start_node='start', end_node='end', mission="critical path"):
        paths = self.find_all_paths(start_node, end_node)
        durations_lst = [0] * len(paths)

        for paths_lst_index, path_list in enumerate(paths):
            for single_path_index, node in enumerate(path_list):
                if node != end_node:
                    # double check for overflow when node=end_node so when path_list[single_path_index +1] won't make problem
                    next_nodes_list = self.activities_dict.get(node)
                    for next_node_dict in next_nodes_list:
                        # because to get time between two  activities we need node and next node inside path
                        next_node_to_find = path_list[single_path_index + 1]
                        if node in self.essential_activities.keys():
                            self.essential_activities[node]
                            # TODO add time by slack time
                            # durations_lst[paths_lst_index] +=
                        for next_node, next_node_duration in next_node_dict.items():
                            if next_node == next_node_to_find:
                                # we search for specific node (next_node_to_find) so we can find duration between node and next_node_to_find
                                durations_lst[paths_lst_index] += next_node_duration
                                break
                                # if we found next node we can break from loop
        print("\nDurations by paths:")
        print(durations_lst)
        max_duration = max(durations_lst)
        print("\nLongest duration is {0}".format(max_duration))
        print("\nLongest path edges:")
        self.project_duration = max_duration
        return paths[durations_lst.index(max_duration)]

    # def find_critical_path(self, tmp_dict, node = 'start', lst_durations = [[]], lst_durations_index=0):
    #     if tmp_dict.get('start') == []:
    #         return lst_durations
    #
    #     if node == 'end':
    #         lst_durations[lst_durations_index].extend(0)
    #         lst_durations_index += 1
    #         return self.find_critical_path(tmp_dict, 'start', lst_durations, lst_durations_index)
    #
    #     for next_node, next_node_duration in tmp_dict.get(node)[0].items():
    #         next_node_str = next_node
    #         lst_durations[lst_durations_index].extend(next_node_duration)
    #     tmp_dict.get(node).pop(0) #remove first dict in list
    #     return self.find_critical_path(tmp_dict, next_node_str, lst_durations, lst_durations_index)

    # def find_critical_path(self):
    #
    #     start_lst = self.activities_dict.get('start')
    #     for connected_to_start_dicts in start_lst:
    #         for connected_node, connected_node_duration in connected_to_start_dicts:
    #             pass
    #     for activity_node, connected_activities in self.activities_dict.items():
    #         # num_of_edges_per_node = len(connected_activities)
    #         for connected_nodes_dict in connected_activities:
    #             for connected_activity_node, connected_activities_duration in connected_nodes_dict.items():
    #                 self.activities_dict.get(connected_activity_node)

    #########Main#########


g = Graph({'start': [{'2': 5}, {'3': 7}, {'4': 6}], '2': [{'5': 3}, {'6': 9}],
           '3': [{'5': 1}, {'7': 4}], '4': [{'7': 6}, {'6': 13}],
           '5': [{'end': 8}], '6': [{'end': 5}], '7': [{'end': 11}], 'end': []})
# g.add_activity('E', 'A', 5 )
print(g)

# g.remove_activity('C')
g.add_activity('5', [{'2': 5}, {'3': 8}])
print("after adding nodes to 5", g)

g.add_activity('3', [{'B': 90}])
print(g)
# g.validate_project()


g.add_activity('10')
print(g)
isolated_nodes = g.find_isolate_activities()
print("\nIsolated nodes:")
for isolated_node in isolated_nodes:
    print(isolated_node)

g.remove_activity('C')
print(g)

g = Graph({'start': [{'2': 5}, {'3': 6}, {'4': 6}], '2': [{'5': 3}],
           '3': [{'5': 1}, {'6': 4}, {'7': 4}], '4': [{'7': 13}],
           '5': [{'end': 8}], '6': [{'end': 5}], '7': [{'end': 11}], 'end': []})
print(g)
isolated_nodes = g.find_isolate_activities()
print("\nIsolated nodes:")
for isolated_node in isolated_nodes:
    print(isolated_node)

g = Graph({'start': [{'B': 5}, {'C': 7}, {'D': 6}], 'B': [{'E': 3}, {'F': 9}],
           'C': [{'E': 1}, {'G': 4}], 'D': [{'G': 6}, {'F': 13}],
           'E': [{'end': 8}], 'F': [{'end': 5}], 'G': [{'end': 11}], 'end': []})

g = Graph({'start': [{'2': 5}, {'3': 6}, {'4': 6}], '2': [{'5': 3}],
           '3': [{'5': 1}, {'6': 4}, {'7': 4}], '4': [{'7': 13}],
           '5': [{'end': 8}], '6': [{'end': 5}], '7': [{'end': 11}], 'end': []})

g = Graph({'start': [{'B': 5}, {'C': 7}, {'D': 6}], 'B': [{'E': 3}, {'F': 9}],
           'C': [{'E': 1}, {'G': 4}], 'D': [{'G': 6}, {'F': 13}],
           'E': [{'end': 8}], 'F': [{'end': 5}], 'G': [{'end': 11}], 'end': []})
print(g)

print("\nAll paths:")
print(g.find_all_paths('start', 'end'))

g = Graph({'start': [{'2': 5}, {'3': 6}, {'4': 6}], '2': [{'5': 3}],
           '3': [{'5': 1}, {'6': 4}, {'7': 4}], '4': [{'7': 13}],
           '5': [{'end': 8}], '6': [{'end': 5}], '7': [{'4': 0}, {'end': 11}], 'end': []})
print(g)
g.essential_activities = {'2': ['3'], 'end': ['2'], '3': ['4']}
g.print_essential_activities()
print("\n All paths:")
print(g.find_all_paths('start', 'end'))
print(g.find_critical_path('start', 'end'))

print("Project duration is")
print(g.project_duration)

# g.fill_essential_nodes_es_ls()
# g.print_essential_activities()
# print(g._es_ls_ef_lf)
#
# g.validate_project()

# TODO check for duplicates
