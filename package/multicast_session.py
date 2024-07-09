
from itertools import combinations

class MulticastSession:
    def __init__(self, librairy, receivers, cache_capacity):
        self.librairy = librairy
        self.receivers = receivers
        self.nb_receivers = len(receivers)
        self.nb_items = len(librairy)
        self.cache_capacity = cache_capacity
        self.t = None
        
    def get_librairy(self):
        return self.librairy
    
    def check_parameters(self):
        '''
        Checks if the given parameters lead to a "valid" scenario, i.e., with integer t=K*g=K*M/N
        
        :param N:	(int) number of files
        :param K:	(int) number of users
        :param M:	(int) cache capacity (in number of files)

        :return:	True/False
        '''
        g = self.cache_capacity/self.nb_items
        t = self.nb_receivers*g
        if t.is_integer():
            self.t = int(t)
            return True
        else:
            return False


    def get_chunks_indices(self):
        '''
        Calculates in how many chunks each file needs to be split, and generates the "indices" (i.e., a list of tuples) for the chunks
        E.g., for N=10,K=5,M=4, it returns the list [(1, 2), (1, 3), (1, 4), (1, 5), (2, 3), (2, 4), (2, 5), (3, 4), (3, 5), (4, 5)]

        :param N:	(int) number of files
        :param K:	(int) number of users
        :param M:	(int) cache capacity (in number of files)

        :return:	(list) a list of tuples, where tuples corresponds to indices for the chunks that the file will be split;
                    the size of the list (i.e., number of indices) is equal to the number of chunks that the files needs to be split 
        '''
        if self.check_parameters():
            indices = list(combinations(range(1,self.nb_receivers+1), self.t))
        else:
            error_message = "t=K*M/N={} is not an integer, choose other parameters, e.g., M={}".format(self.nb_receivers*self.cache_capacity/self.nb_items, int(int(self.nb_receivers*self.cache_capacity/self.nb_items)*self.nb_items/self.nb_receivers))
            raise Exception(error_message)

        return indices

    def get_indices_per_user_cache(self,indices):
        '''
        Calculates the list of indices (i.e., which chunks) that each user cache should contain
        
        :param K:	(int) number of users (each user has an ID from 1 ... K)
        :param indices: (list) a list of tuples, where tuples correspond to indices

        :return:	(dict) a dictionary with keys the user ID (from 1 to K) and values a list of indices (subset of the given list of indices)
        '''
        ### calculate indices of caches
        caches = {}
        for i in range(1,self.nb_receivers+1):
            caches[i] = [ind for ind in indices if i in ind]

        return caches


    def get_list_of_xor_packets_for_transmission(self,requested_files):
        '''
        Calculates the packets that the transmitter has to do to serve the given list of requests, 
        and the XOR operations that are needed for each packet 

        :param requested_files:	(dict) a dictionary with the requests: format user ID (key) -->  file ID (value)
        :param K:	(int) number of users
        :param t:	(int) the t parameter of the system

        :return:	(list) a list of lists. 
                    In the list, each item corresponds to each transmission that has to be done;
                    each item is a list of tuples;
                    each tuple contains information about the file (tuple[0]) and the index (tuple[1]) that need to be XOR'ed.
                    For example: [ [(1,(2,3)),(2,(1,3),...)], [...], ... ]
                    The first transmission will XOR the chunk(2,3) of file1 with the chunk(1,3) of file2, ...
        '''
        list_of_xor_packets = []
        requesting_users = list(requested_files.keys())
        all_users = list(range(1,self.nb_receivers+1))
        list_of_xor_combinations = list(combinations(all_users,self.t+1))
        for xor_combination in list_of_xor_combinations:
            chunks_to_xor = []
            for user in xor_combination:
                if user in requesting_users:
                    file = requested_files[user]
                    chunk = tuple([i for i in xor_combination if i != user])
                    chunks_to_xor.append((file,chunk))
                else:
                    chunks_to_xor.append(('na','na'))
            list_of_xor_packets.append(chunks_to_xor)
        return list_of_xor_packets
