import numpy as np
import random


def preprocessing(obj_path):
    # Variables
    faces = []
    vertices = []
    gates = {}
    valences = {}
    patches = {}
    active_vertices = set()
    
    # Retrieve the data from the obj file
    with open(obj_path) as file:
        current_vertex = 1
        # Loop over the lines of the obj file
        for line in file:
            # Case of a vertex
            if line[0] == 'v':
                # Store the coordinates x, y, z
                x, y, z = line.split(' ')[1:]
                vertices.append([float(x), float(y), float(z)])
                active_vertices.add(current_vertex)
                current_vertex += 1

            # Case of a face
            elif line[0] == 'f':
                # The indices of the face vertices
                a, b, c = line.split(' ')[1:]
                a, b, c = int(a), int(b), int(c)
                faces.append([a, b, c])

                # Add the different gates
                gates[(a, b)] = c
                gates[(b, c)] = a
                gates[(c, a)] = b

                # Update the valences
                if valences.get(a) is None:
                    valences[a] = 1
                else:
                    valences[a] += 1

                if valences.get(b) is None:
                    valences[b] = 1
                else:
                    valences[b] += 1

                if valences.get(c) is None:
                    valences[c] = 1
                else:
                    valences[c] += 1

                # Add the patches
                if patches.get(a) is None:
                    patches[a] = [(b, c)]
                else:
                    patches[a].append((b, c))

                if patches.get(b) is None:
                    patches[b] = [(c, a)]
                else:
                    patches[b].append((c, a))

                if patches.get(c) is None:
                    patches[c] = [(a, b)]
                else:
                    patches[c].append((a, b))

    # Order the edges in the patches
    for vertex, edges in patches.items():
        start, end = edges.pop(0)
        chained_list = [start, end]

        while len(edges) > 1:
            for edge in edges:
                if edge[0] == end:
                    end = edge[1]
                    chained_list.append(end)
                    break
            edges.remove(edge)

        patches[vertex] = np.array(chained_list)

    return gates, valences, patches, active_vertices, vertices

def decimating_conquest(gates, valences, patches, active_vertices, it):

    faces_status = {}
    vertices_status = {}
    plus_minus = {}

    # Choose a random gate
    if it == 0:
        first_gate = (158, 159)
    elif it == 1:
        first_gate = (152, 149)
    elif it == 2:
        first_gate = (34, 38)
    else:
        first_gate = random.choice(list(gates.keys()))
    left, right = first_gate
    plus_minus[left] = '-'
    plus_minus[right] = '+'

    # Create the fifo
    fifo = [first_gate]

    # Loop over the model
    while len(fifo) > 0:

        # Retrieve the first element of the fifo
        gate = fifo.pop(0)
        left, right = gate
        vertices_status[left] = 'conquered'
        vertices_status[right] = 'conquered'


        # Retrieve the front vertex
        front = gates[gate]

        # conquered or null
        if faces_status.get(gate) is not None:
            print('*', end='')
            continue

        elif valences[front] <= 6 and vertices_status.get(front) is None:
            print('.', end='')

            # Retrieve the border of the patch
            chain = patches[front]

            # Tag all the vertices as conquered
            for vertex in chain:
                vertices_status[vertex] = 'conquered'

            # Add the following gates to the fifo
            # and tag the inner faces as conquered
            i = np.where(chain == right)[0][0]
            chain = np.append(chain[i:], chain[:i])
            # print(chain)
            for gate in zip(chain[1:], chain[:-1]):
                # print(gate)
                fifo.append(gate)
                faces_status[(gate[-1], gate[0])] = 'conquered'
            # print("stop")

            # Remove the front vertex
            # print(front)
            active_vertices.remove(front)

            # Remove the old gates
            for vertex in chain:
                gates.pop((front, vertex))
                gates.pop((vertex, front))

            # Retriangulation
            valences, patches, gates = retriangulation(chain, valences, left, right, gates, patches, front, plus_minus)

        elif (vertices_status.get(front) is None and valences[front] > 6) or (
                vertices_status.get(front) == 'conquered'):
            print('o', end='')

            # Set the front face to null
            faces_status[gate] = 'null'

            if plus_minus.get(front) is None:
                plus_minus[front] = '+'

            # Add the other edges to the fifo
            fifo.append((front, right))
            fifo.append((left, front))

        else:
            print("ERROR: ELSE (decimating conquest)")

    return valences, patches, gates

def retriangulation(chain, valences, left, right, gates, patches, front, plus_minus):
    # Retrieve the information to start the retriangulation
    valence = valences[front]
    left_sign = plus_minus[left]
    right_sign = plus_minus[right]

    # Select the right case
    if valence == 3:
        # Update the valences
        for vertex in chain:
            valences[vertex] -= 1

        # Update the faces
        new_front = chain[1]
        gates[(left, right)] = new_front
        gates[(right, new_front)] = left
        gates[(new_front, left)] = right

        # Update the patches
        for vertex in chain:
            patches[vertex] = patches[vertex][patches[vertex] != front]

        # Update the signs
        if plus_minus.get(new_front) is None:
            if left_sign == '+' and right_sign == '+':
                plus_minus[new_front] = '-'
            else:
                plus_minus[new_front] = '+'
                

    elif valence == 4:
        if right_sign == '-':
            # Update the signs
            if plus_minus.get(chain[1]) is None:
                plus_minus[chain[1]] = '+'
            if plus_minus.get(chain[2]) is None:
                plus_minus[chain[2]] = '-'

            # Update the faces
            gates[(left, right)] = chain[1]
            gates[(right, chain[1])] = left
            gates[(chain[1], chain[2])] = left
            gates[(chain[2], left)] = chain[1]

            # Add the new gates
            gates[(left, chain[1])] = chain[2]
            gates[(chain[1], left)] = right

            # Update the valences
            valences[right] -= 1
            valences[chain[2]] -= 1

            # Update the patches
            patches[right] = patches[right][patches[right] != front]
            patches[chain[2]] = patches[chain[2]][patches[chain[2]] != front]
            patches[left][np.where(patches[left] == front)[0]] = chain[1]
            patches[chain[1]][np.where(patches[chain[1]] == front)[0]] = left

        else:
            # Update the signs
            if plus_minus.get(chain[1]) is None:
                plus_minus[chain[1]] = '-'
            if plus_minus.get(chain[2]) is None:
                plus_minus[chain[2]] = '+'

            # Update the faces
            gates[(left, right)] = chain[2]
            gates[(right, chain[1])] = chain[2]
            gates[(chain[1], chain[2])] = right
            gates[(chain[2], left)] = right

            # Add the new gates
            gates[(right, chain[2])] = left
            gates[(chain[2], right)] = chain[1]

            # Update the valences
            valences[left] -= 1
            valences[chain[1]] -= 1

            # Update the patches
            patches[left] = patches[left][patches[left] != front]
            patches[chain[1]] = patches[chain[1]][patches[chain[1]] != front]
            patches[right][np.where(patches[right] == front)[0]] = chain[2]
            patches[chain[2]][np.where(patches[chain[2]] == front)[0]] = right

    elif valence == 5:
        if right_sign == '-':
            # Update the signs
            if plus_minus.get(chain[1]) is None:
                plus_minus[chain[1]] = '+'
            if plus_minus.get(chain[2]) is None:
                plus_minus[chain[2]] = '-'
            if plus_minus.get(chain[3]) is None:
                plus_minus[chain[3]] = '+'

            # Update the faces
            gates[(left, right)] = chain[1]
            gates[(right, chain[1])] = left
            gates[(chain[1], chain[2])] = chain[3]
            gates[(chain[2], chain[3])] = chain[1]
            gates[(chain[3], left)] = chain[1]

            # Add the new gates
            gates[(left, chain[1])] = chain[3]
            gates[(chain[1], left)] = right
            gates[(chain[3], chain[1])] = chain[2]
            gates[(chain[1], chain[3])] = left

            # Update the valences
            valences[right] -= 1
            valences[chain[1]] += 1
            valences[chain[2]] -= 1

            # Update the patches
            patches[right] = patches[right][patches[right] != front]

            patch = patches[chain[1]]
            i = np.where(patch == front)[0][0]
            patch = patch[patch != front]
            patches[chain[1]] = np.insert(patch, [i, i], [chain[3], left])

            patches[chain[2]] = patches[chain[2]][patches[chain[2]] != front]
            patches[chain[3]][np.where(patches[chain[3]] == front)[0]] = chain[1]
            patches[left][np.where(patches[left] == front)[0]] = chain[1]

        elif left_sign == '-':
            # Update the signs
            if plus_minus.get(chain[1]) is None:
                plus_minus[chain[1]] = '+'
            if plus_minus.get(chain[2]) is None:
                plus_minus[chain[2]] = '-'
            if plus_minus.get(chain[3]) is None:
                plus_minus[chain[3]] = '+'

            # Update the faces
            gates[(left, right)] = chain[3]
            gates[(right, chain[1])] = chain[3]
            gates[(chain[1], chain[2])] = chain[3]
            gates[(chain[2], chain[3])] = chain[1]
            gates[(chain[3], left)] = right

            # Add the new gates
            gates[(right, chain[3])] = left
            gates[(chain[3], right)] = chain[1]
            gates[(chain[3], chain[1])] = chain[2]
            gates[(chain[1], chain[3])] = right

            # Update the valences
            valences[chain[2]] -= 1
            valences[chain[3]] += 1
            valences[left] -= 1

            # Update the patches
            patches[right][np.where(patches[right] == front)[0]] = chain[3]
            patches[chain[1]][np.where(patches[chain[1]] == front)[0]] = chain[3]
            patches[chain[2]] = patches[chain[2]][patches[chain[2]] != front]

            patch = patches[chain[3]]
            i = np.where(patch == front)[0][0]
            patch = patch[patch != front]
            patches[chain[3]] = np.insert(patch, [i, i], [right, chain[1]])

            patches[left] = patches[left][patches[left] != front]

        else:
            # Update the signs
            if plus_minus.get(chain[1]) is None:
                plus_minus[chain[1]] = '-'
            if plus_minus.get(chain[2]) is None:
                plus_minus[chain[2]] = '+'
            if plus_minus.get(chain[3]) is None:
                plus_minus[chain[3]] = '-'

            # Update the faces
            gates[(left, right)] = chain[2]
            gates[(right, chain[1])] = chain[2]
            gates[(chain[1], chain[2])] = right
            gates[(chain[2], chain[3])] = left
            gates[(chain[3], left)] = chain[2]

            # Add the new gates
            gates[(right, chain[2])] = left
            gates[(chain[2], right)] = chain[1]
            gates[(chain[2], left)] = right
            gates[(left, chain[2])] = chain[3]

            # Update the valences
            valences[chain[1]] -= 1
            valences[chain[2]] += 1
            valences[chain[3]] -= 1

            # Update the patches
            patches[right][np.where(patches[right] == front)[0]] = chain[2]
            patches[chain[1]] = patches[chain[1]][patches[chain[1]] != front]

            patch = patches[chain[2]]
            i = np.where(patch == front)[0][0]
            patch = patch[patch != front]
            patches[chain[2]] = np.insert(patch, [i, i], [left, right])

            patches[chain[3]] = patches[chain[3]][patches[chain[3]] != front]
            patches[left][np.where(patches[left] == front)[0]] = chain[2]

    elif valence == 6:

        if right_sign == '-':
            # Update the signs
            if plus_minus.get(chain[1]) is None:
                plus_minus[chain[1]] = '+'
            if plus_minus.get(chain[2]) is None:
                plus_minus[chain[2]] = '-'
            if plus_minus.get(chain[3]) is None:
                plus_minus[chain[3]] = '+'
            if plus_minus.get(chain[4]) is None:
                plus_minus[chain[4]] = '-'

            # Update the faces
            gates[(left, right)] = chain[1]
            gates[(right, chain[1])] = left
            gates[(chain[1], chain[2])] = chain[3]
            gates[(chain[2], chain[3])] = chain[1]
            gates[(chain[3], chain[4])] = left
            gates[(chain[4], left)] = chain[3]

            # Add the new gates
            gates[(left, chain[1])] = chain[3]
            gates[(chain[1], left)] = right
            gates[(chain[3], chain[1])] = chain[2]
            gates[(chain[1], chain[3])] = left
            gates[(left, chain[3])] = chain[4]
            gates[(chain[3], left)] = chain[1]

            # Update the valences
            valences[right] -= 1
            valences[chain[1]] += 1
            valences[chain[2]] -= 1
            valences[chain[3]] += 1
            valences[chain[4]] -= 1
            valences[left] += 1

            # Update the patches
            patches[right] = patches[right][patches[right] != front]

            patch = patches[chain[1]]
            i = np.where(patch == front)[0][0]
            patch = patch[patch != front]
            patches[chain[1]] = np.insert(patch, [i, i], [chain[3], left])

            patches[chain[2]] = patches[chain[2]][patches[chain[2]] != front]

            patch = patches[chain[3]]
            i = np.where(patch == front)[0][0]
            patch = patch[patch != front]
            patches[chain[3]] = np.insert(patch, [i, i], [left, chain[1]])

            patches[chain[4]] = patches[chain[4]][patches[chain[4]] != front]

            patch = patches[left]
            i = np.where(patch == front)[0][0]
            patch = patch[patch != front]
            patches[left] = np.insert(patch, [i, i], [chain[1], chain[3]])

        else:
            # Update the signs
            if plus_minus.get(chain[1]) is None:
                plus_minus[chain[1]] = '-'
            if plus_minus.get(chain[2]) is None:
                plus_minus[chain[2]] = '+'
            if plus_minus.get(chain[3]) is None:
                plus_minus[chain[3]] = '-'
            if plus_minus.get(chain[4]) is None:
                plus_minus[chain[4]] = '+'

            # Update the faces
            gates[(left, right)] = chain[4]
            gates[(right, chain[1])] = chain[2]
            gates[(chain[1], chain[2])] = right
            gates[(chain[2], chain[3])] = chain[4]
            gates[(chain[3], chain[4])] = chain[2]
            gates[(chain[4], left)] = right

            # Add the new gates
            gates[(right, chain[4])] = left
            gates[(chain[4], right)] = chain[2]
            gates[(chain[4], chain[2])] = chain[3]
            gates[(chain[2], chain[4])] = right
            gates[(right, chain[2])] = chain[4]
            gates[(chain[2], right)] = chain[1]

            # Update the valences
            valences[right] += 1
            valences[chain[1]] -= 1
            valences[chain[2]] += 1
            valences[chain[3]] -= 1
            valences[chain[4]] += 1
            valences[left] -= 1

            # Update the patches
            patch = patches[right]
            i = np.where(patch == front)[0][0]
            patch = patch[patch != front]
            patches[right] = np.insert(patch, [i, i], [chain[2], chain[4]])

            patches[chain[1]] = patches[chain[1]][patches[chain[1]] != front]

            patch = patches[chain[2]]
            i = np.where(patch == front)[0][0]
            patch = patch[patch != front]
            patches[chain[2]] = np.insert(patch, [i, i], [chain[4], right])

            patches[chain[3]] = patches[chain[3]][patches[chain[3]] != front]

            patch = patches[chain[4]]
            i = np.where(patch == front)[0][0]
            patch = patch[patch != front]
            patches[chain[4]] = np.insert(patch, [i, i], [right, chain[2]])

            patches[left] = patches[left][patches[left] != front]
    return valences, patches, gates

def cleaning_conquest(gates, patches, valences, active_vertices, fifo):
    # Cleaning Conquest
    faces_status = {}
    vertices_status = {}
    done = set()
    
    # Choose a random gate
    for vertex in active_vertices:
        if valences[vertex] == 3:
            chain = patches[vertex]
            break
    else:
        return
            
    first_gate = (chain[0],chain[1])

    # Create the fifo
    fifo.append(first_gate)

    # Loop over the model
    while len(fifo) > 0:
        # Retrieve the first element of the fifo
        gate = fifo.pop(0)
        if gate in done:
            continue
        else:
            done.add(gate)

        # Retrieve the front vertex
        front = gates[gate]
        chain = patches[front]
        left, right = gate

        # conquered or null
        if faces_status.get(gate) is not None:
            print('*', end='')
            continue

        elif valences[front] == 3 and vertices_status.get(front) is None:
            print('.', end='')

           # Remove the vertex
            active_vertices.remove(front)
            
            for left,right in fifo.copy():
                if left == front or right == front:
                    fifo.remove((left,right))

            # Update the valences
            for point in chain:
                valences[point] -= 1
                # Remove the old gates
                gates.pop((front, point))
                gates.pop((point, front))

            # Update the faces
            gates[(chain[0], chain[1])] = chain[2]
            gates[(chain[1], chain[2])] = chain[0]
            gates[(chain[2], chain[0])] = chain[1]

            # Update the patches
            for point in chain:
                patches[point] = patches[point][patches[point] != front]
                vertices_status[point] = 'conquered'

            # Update face status        
            faces_status[(chain[1],chain[0])] = 'conquered'
            faces_status[(chain[2],chain[1])] = 'conquered'

            # Update fifo
            front_1 = gates[(chain[1],chain[0])]
            front_2 = gates[(chain[2],chain[1])]
            fifo.append((front_1, chain[0]))
            fifo.append((chain[1], front_1))
            fifo.append((front_2, chain[1]))
            fifo.append((chain[2], front_2))
                

        elif valences[front] <= 6 and vertices_status.get(front) is None:
            print("-", end='')
            i = np.where(chain == right)[0][0]
            chain = np.append(chain[i:], chain[:i])
            # print(chain)
            for gate in zip(chain[1:], chain[:-1]):
                # print(gate)
                fifo.append(gate)
                faces_status[(gate[-1], gate[0])] = 'conquered'

        elif (vertices_status.get(front) is None and valences[front] > 6) or (
                vertices_status.get(front) == 'conquered'):
            print('o', end='')

            # Set the front face to null
            faces_status[gate] = 'null'

            # Add the other edges to the fifo
            fifo.append((front, right))
            fifo.append((left, front))

def write_obj(path, active_vertices, gates, vertices):
    new_indices = {}
    local_copy = gates.copy()
    with open(path, 'w') as file:
        for k, vertex in enumerate(active_vertices):
            x, y, z = vertices[vertex-1]
            file.write('v {} {} {}\n'.format(x, y, z))
            new_indices[vertex] = k + 1

        for gate in gates.copy():
            left, right = gate
            try:
                front = local_copy[gate]
                local_copy.pop(gate)
                local_copy.pop((right, front))
                local_copy.pop((front, left))
                file.write('f {} {} {}\n'.format(
                    new_indices[left], new_indices[right], new_indices[front]))
            except KeyError:
                continue


def sew_conquest(gates, patches, active_vertices, valences):
    to_sew = {}
    recto_verso = []
    for gate, front in gates.copy().items():
        left, right = gate
        if gates.get((right,left)) is None:
            print('!!!!!!!!!!')
            to_sew[right] = left
            
        elif front == gates[(right,left)] and valences[front] == 2:
            print('cvocouucouc')
            try:
                active_vertices.remove(front)

                #update gates
                gates.remove((right,left))
                gates.remove((left, right))
                gates.remove((right,front))
                gates.remove((left, front))
                gates.remove((front,right))
                gates.remove((front,left)) 
                
                #update patches
                patches[right] = patches[right][patches[right] != front]
                patches[left] = patches[left][patches[left] != front]
                
                recto_verso.append(gate)
                recto_verso.append((right, left))
            except KeyError:
                continue
    
    for left, right in recto_verso:
        print('\t!!!\t')
        gates[(right, to_sew[right])] = left
        gates[(to_sew[right], left)] = right
        gates[(left, right)] = to_sew[right]