from deap import tools
from deap import gp
from deap import algorithms

def MPIMigRing(comm, population, numMigrants, selection, replacement, logger=None):
    """Perform a ring migration between the *populations*.
       In this case, each MPI rank is expected to have 1 population.
       So the migrants just get passed to the next MPI rank.
       The migration first
       select *k* emigrants from each population using the specified *selection*
       operator and then replace *k* individuals from the associated population
       in the *migarray* by the emigrants. If no *replacement* operator is
       specified, the immigrants will replace the emigrants of the population,
       otherwise, the immigrants will replace the individuals selected by the
       *replacement* operator. The migration array, if provided, shall contain
       each population's index once and only once. If no migration array is
       provided, it defaults to a serial ring migration (1 -- 2 -- ... -- n --
       1). Selection and replacement function are called using the signature
       ``selection(populations[i], k)`` and ``replacement(populations[i], k)``.
       It is important to note that the replacement strategy must select *k*
       **different** individuals. For example, using a traditional tournament for
       replacement strategy will thus give undesirable effects, two individuals
       will most likely try to enter the same slot.
    
       :param comm: An MPI commicator.  It's assumed that the number of populations
                    is equal to the size, and that the population in this process
                    in # rank.
       :param population: The population to select from and insert to
       :param numMigrants: The number of emmigrants to send, and immigrants to expect
       :param selection:   The algorithm to select individuals to emmigrate
       :param replacement: The function to use to select which individuals will
                        be replaced. If :obj:`None` (default) the individuals
                        that leave the population are directly replaced.
       :param logger:      PrintLogger class.  Optionally prints out debugging data.
    """
    rank = comm.Get_rank()
    size = comm.Get_size()
    emigrants = selection(population, numMigrants)
    toBeReplaced = emigrants      #if not replacement selector was defined, replace the emigrants
    if not replacement is None: #Otherwise use the replacement selector
        toBeReplaced = replacement(population, numMigrants)


    logger.printOut(5, "MPIMigRing: toBeReplaced on rank: %d" % (rank))
    logger.printPopulation(5, toBeReplaced)
    
    req = comm.isend(emigrants, dest=(rank+1)%size)  #Send and recv in a ring
    immigrants = comm.recv(source=(rank-1)%size)
    req.wait()

    logger.printOut(5, "MPIMigRing: immigrants on rank: %d" % (rank))
    logger.printPopulation(5, immigrants)
    
    for ii, deadInv in enumerate(toBeReplaced):
        try:
            indx = population.index(deadInv)
        except:
            population.append(immigrants[ii])  #Sometimes the index call fails for some reason.  If so, just append the immigrant.
        else:
            population[indx] = immigrants[ii]  #replace the guy we picked to leave with the new arrival
