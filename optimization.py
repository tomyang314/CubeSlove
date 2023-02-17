import re


def optimization(s):
    table = ""

    index = find_index(s)

    while index >= 0:
        flag = " "
        if s[index: index + 5] == "U' D " or s[index: index + 4] == "D U'":
            s = s.replace(s[index: index + 4], 'Z', 1)
            flag = 'Z'
        elif s[index: index + 4] == "U D'" or s[index: index + 5] == "D' U ":
            s = s.replace(s[index: index + 4], "Z'", 1)
            flag = "Z'"
        elif s[index: index + 5] == "U2 D2" or s[index: index + 5] == "D2 U2":
            s = s.replace(s[index: index + 5], "Z2", 1)
            flag = "Z2"

        elif s[index: index + 5] == "L' R " or s[index: index + 4] == "R L'":
            s = s.replace(s[index: index + 4], "Y'", 1)
            flag = "Y'"
        elif s[index: index + 4] == "L R'" or s[index: index + 5] == "R' L ":
            s = s.replace(s[index: index + 4], 'Y', 1)
            flag = 'Y'
        elif s[index: index + 5] == "L2 R2" or s[index: index + 5] == "R2 L2":
            s = s.replace(s[index: index + 5], "Y2", 1)
            flag = "Y2"

        elif s[index: index + 5] == "F' B " or s[index: index + 4] == "B F'":
            s = s.replace(s[index: index + 4], 'X', 1)
            flag = 'X'
        elif s[index: index + 4] == "F B'" or s[index: index + 5] == "B' F ":
            s = s.replace(s[index: index + 4], "X'", 1)
            flag = "X'"
        elif s[index: index + 5] == "F2 B2" or s[index: index + 5] == "B2 F2":
            s = s.replace(s[index: index + 5], "X2", 1)
            flag = "X2"

        left = s[0: index + 2]
        right = s[index + 2:]
        table += left
        s = right
        s_new = ""
        if flag == 'X':
            for val in re.split(r"[ ]+", s):
                if val.find('R') != -1:
                    val = val.replace('R', 'D') + ' '
                    s_new += val
                elif val.find('L') != -1:
                    val = val.replace('L', 'U') + ' '
                    s_new += val
                elif val.find('U') != -1:
                    val = val.replace('U', 'R') + ' '
                    s_new += val
                elif val.find('D') != -1:
                    val = val.replace('D', 'L') + ' '
                    s_new += val
                else:
                    s_new += val + ' '
            s = s_new

        elif flag == "X'":
            for val in re.split(r"[ ]+", s):
                if val.find('R') != -1:
                    val = val.replace('R', 'U') + ' '
                    s_new += val
                elif val.find('L') != -1:
                    val = val.replace('L', 'D') + ' '
                    s_new += val
                elif val.find('U') != -1:
                    val = val.replace('U', 'L') + ' '
                    s_new += val
                elif val.find('D') != -1:
                    val = val.replace('D', 'R') + ' '
                    s_new += val
                else:
                    s_new += val + ' '
            s = s_new

        elif flag == "X2":
            for val in re.split(r"[ ]+", s):
                if val.find('R') != -1:
                    val = val.replace('R', 'L') + ' '
                    s_new += val
                elif val.find('L') != -1:
                    val = val.replace('L', 'R') + ' '
                    s_new += val
                elif val.find('U') != -1:
                    val = val.replace('U', 'D') + ' '
                    s_new += val
                elif val.find('D') != -1:
                    val = val.replace('D', 'U') + ' '
                    s_new += val
                else:
                    s_new += val + ' '
            s = s_new

        elif flag == 'Y':
            for val in re.split(r"[ ]+", s):
                if val.find('F') != -1:
                    val = val.replace('F', 'U') + ' '
                    s_new += val
                elif val.find('B') != -1:
                    val = val.replace('B', 'D') + ' '
                    s_new += val
                elif val.find('U') != -1:
                    val = val.replace('U', 'B') + ' '
                    s_new += val
                elif val.find('D') != -1:
                    val = val.replace('D', 'F') + ' '
                    s_new += val
                else:
                    s_new += val + ' '
            s = s_new

        elif flag == "Y'":
            for val in re.split(r"[ ]+", s):
                if val.find('F') != -1:
                    val = val.replace('F', 'D') + ' '
                    s_new += val
                elif val.find('B') != -1:
                    val = val.replace('B', 'U') + ' '
                    s_new += val
                elif val.find('U') != -1:
                    val = val.replace('U', 'F') + ' '
                    s_new += val
                elif val.find('D') != -1:
                    val = val.replace('D', 'B') + ' '
                    s_new += val
                else:
                    s_new += val + ' '
            s = s_new

        elif flag == "Y2":
            for val in re.split(r"[ ]+", s):
                if val.find('F') != -1:
                    val = val.replace('F', 'B') + ' '
                    s_new += val
                elif val.find('B') != -1:
                    val = val.replace('B', 'F') + ' '
                    s_new += val
                elif val.find('U') != -1:
                    val = val.replace('U', 'D') + ' '
                    s_new += val
                elif val.find('D') != -1:
                    val = val.replace('D', 'U') + ' '
                    s_new += val
                else:
                    s_new += val + ' '
            s = s_new

        elif flag == 'Z':
            for val in re.split(r"[ ]+", s):
                if val.find('F') != -1:
                    val = val.replace('F', 'L') + ' '
                    s_new += val
                elif val.find('B') != -1:
                    val = val.replace('B', 'R') + ' '
                    s_new += val
                elif val.find('R') != -1:
                    val = val.replace('R', 'F') + ' '
                    s_new += val
                elif val.find('L') != -1:
                    val = val.replace('L', 'B') + ' '
                    s_new += val
                else:
                    s_new += val + ' '
            s = s_new

        elif flag == "Z'":
            for val in re.split(r"[ ]+", s):
                if val.find('F') != -1:
                    val = val.replace('F', 'R') + ' '
                    s_new += val
                elif val.find('B') != -1:
                    val = val.replace('B', 'L') + ' '
                    s_new += val
                elif val.find('R') != -1:
                    val = val.replace('R', 'B') + ' '
                    s_new += val
                elif val.find('L') != -1:
                    val = val.replace('L', 'F') + ' '
                    s_new += val
                else:
                    s_new += val + ' '
            s = s_new

        elif flag == "Z2":
            for val in re.split(r"[ ]+", s):
                if val.find('F') != -1:
                    val = val.replace('F', 'B') + ' '
                    s_new += val
                elif val.find('B') != -1:
                    val = val.replace('B', 'F') + ' '
                    s_new += val
                elif val.find('R') != -1:
                    val = val.replace('R', 'L') + ' '
                    s_new += val
                elif val.find('L') != -1:
                    val = val.replace('L', 'R') + ' '
                    s_new += val
                else:
                    s_new += val + ' '
            s = s_new

        index = find_index(s)

    table += s
    # print(table)

    return table


def find_index(string):
    sequence = []
    if string.find("U' D ") != -1:
        sequence.append(string.find("U' D "))
    if string.find("D U' ") != -1:
        sequence.append(string.find("D U' "))
    if string.find("U D' ") != -1:
        sequence.append(string.find("U D' "))
    if string.find("D' U ") != -1:
        sequence.append(string.find("D' U "))
    if string.find("U2 D2") != -1:
        sequence.append(string.find("U2 D2"))
    if string.find("D2 U2") != -1:
        sequence.append(string.find("D2 U2"))

    if string.find("L' R ") != -1:
        sequence.append(string.find("L' R "))
    if string.find("R L' ") != -1:
        sequence.append(string.find("R L' "))
    if string.find("L R' ") != -1:
        sequence.append(string.find("L R' "))
    if string.find("R' L ") != -1:
        sequence.append(string.find("R' L "))
    if string.find("L2 R2") != -1:
        sequence.append(string.find("L2 R2"))
    if string.find("R2 L2") != -1:
        sequence.append(string.find("R2 L2"))

    if string.find("F' B ") != -1:
        sequence.append(string.find("F' B "))
    if string.find("B F' ") != -1:
        sequence.append(string.find("B F' "))
    if string.find("F B' ") != -1:
        sequence.append(string.find("F B' "))
    if string.find("B' F ") != -1:
        sequence.append(string.find("B' F "))
    if string.find("F2 B2") != -1:
        sequence.append(string.find("F2 B2"))
    if string.find("B2 F2") != -1:
        sequence.append(string.find("B2 F2"))

    if not sequence:
        return -1

    return min(sequence)

