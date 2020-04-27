def findExpandingSystems(systems,targetSystem):
    for sys in systems:
        if sys['name']==targetSystem:
            print(targetSystem)
        else:
            print('Target not found')

systems = {}
targetSystem = 'Meliae'