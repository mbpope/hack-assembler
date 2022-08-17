# Hack Assembler
# Author: Micah Pope
# August 2022

# This is a script to interpret Hack assembly into 
# machine language for the Hack computer architecture 
# built in nand2tetris (see nand2tetris.org for more info)

# Possible improvements:

# - currently the assembler takes three passes through the given
#   program, this could be easily cut down to two by moving
#   the stripWhitespace step into firstPass
# - there's some really ugly unpythonic string processing going on 
#   in various places that I'm too lazy and stupid to fix

import sys

# pre-defined symbols (will be combined with
# user-defined symbols as script iterates)
symbol_table = {
    "SP":     "0",
    "LCL":    "1",
    "ARG":    "2",
    "THIS":   "3",
    "THAT":   "4",
    "R0":     "0",
    "R1":     "1",
    "R2":     "2",
    "R3":     "3",
    "R4":     "4",
    "R5":     "5",
    "R6":     "6",
    "R7":     "7",
    "R8":     "8",
    "R9":     "9",
    "R10":    "10",
    "R11":    "11",
    "R12":    "12",
    "R13":    "13",
    "R14":    "14",
    "R15":    "15",
    "SCREEN": "16384",
    "KBD":    "24576"
}

def main():
    """
    - Get assembly
    - Strip whitespace and comments
    - Parse assembly
    - Write machine language to filename.hack
    """

    filename = sys.argv[1]
    asm = getAssembly(filename)
    asm = stripWhitespace(asm)
    machine_code = parser(asm)
    writeMachineCode(machine_code, filename)

def getAssembly(filename):
    """
    Returns line-by-line array of .asm file supplied by filename
    """

    asm_arr= []
    asm = open(filename, "r")
    for i in asm:
        asm_arr.append(i)
    asm.close()
    return asm_arr

def writeMachineCode(machine_code, filename):
    """
    Write finished machine code to a file of the same
    filename as the input with the .hack extension
    """

    simple_filename = filename.split(".")[0]
    new_filename = simple_filename + ".hack"
    new_file = open(new_filename, "w")
    for elt in machine_code:
        new_file.write(elt + "\n")
    new_file.close()

def parser(asm):
    """
    Top level parser function that runs firstPass and secondPass
    """
    asm = firstPass(asm)
    return secondPass(asm)

def firstPass(asm):
    """
    Returns asm array with goto markers removed and stowed in symbol_table
    """
    new_asm = []
    inst_ptr = 0
    for inst in asm:
        # if the line is a goto marker...
        if inst[0] == "(":
            label_name = inst.replace("(", "").replace(")", "")
            symbol_table[label_name] = str(inst_ptr)
        else:
            new_asm.append(inst)
            inst_ptr += 1
    return new_asm

def secondPass(asm):
    """
    Return translated assembly
    """

    translated = []
    n = 16
    for inst in asm:
        # "A" instruction
        if inst[0] == "@":
            # if the instruction contains any alphabetic characters...
            if any(c.isalpha() for c in inst[1:]):
                # if it's not already in the symbol table...
                if inst[1:] not in symbol_table:
                    symbol_table[inst[1:]] = str(n)
                    n += 1
                # change the symbol into an actual address based on the symbol table
                inst = "@" + symbol_table[inst[1:]]
            # take everything after the @ and convert
            # it into a 16 bit zero-padded binary string
            a_inst = format(int(inst[1:]), "016b")
            translated.append(a_inst)
        else:
            translated.append(createCInst(inst))
                                        
            
    return translated

def createCInst(inst):
    jmp_table = {
        None:  "000",
        "JGT": "001",
        "JEQ": "010",
        "JGE": "011",
        "JLT": "100",
        "JNE": "101",
        "JLE": "110",
        "JMP": "111"
    }

    # There's gotta be a better way than having multiple
    # keys line up with duplicate values, but I'm too lazy
    # to find said better way
    comp_table = {
        "0":   "101010",
        "1":   "111111",
        "-1":  "111010",
        "D":   "001100",
        "A":   "110000",
        "M":   "110000",
        "!D":  "001101",
        "!A":  "110001",
        "!M":  "110001",
        "-D":  "001111",
        "-A":  "110011",
        "-M":  "110011",
        "D+1": "011111",
        "A+1": "110111",
        "M+1": "110111",
        "D-1": "001110",
        "A-1": "110010",
        "M-1": "110010",
        "D+A": "000010",
        "D+M": "000010",
        "D-A": "010011",
        "D-M": "010011",
        "A-D": "000111",
        "M-D": "000111",
        "D&A": "000000",
        "D&M": "000000",
        "D|A": "010101",
        "D|M": "010101"
    }

    # "C" instructions are of the format:
    # 1 1 1 a c1 c2 c3 c4 c5 c6 d1 d2 d3 j1 j2 j3
    dest, comp, jmp = parseCInstAsm(inst)
    a = "1" if "M" in comp else "0"
    d1 = d2 = d3 = "0"
    if dest:
        d1 = "1" if "A" in dest else "0"
        d2 = "1" if "D" in dest else "0"
        d3 = "1" if "M" in dest else "0"
    comp = comp_table[comp]
    jmp = jmp_table[jmp]
    
    return "111" + a + comp + d1 + d2 + d3 + jmp
    

def parseCInstAsm(inst):
    """
    Returns separated dest, comp, and jmp values
    """

    # I am aware this is incredibly ugly. Look away.
    dest = comp = jmp = ""
    jmp_split = []
    dest_split = inst.split("=")
    dest_exists = 1 if len(dest_split) == 2 else 0
    dest = dest_split[0] if dest_exists else None
    jmp_split = dest_split[dest_exists].split(";")
    jmp = jmp_split[1] if len(jmp_split) == 2 else None
    comp = jmp_split[0]

    return dest, comp, jmp


def stripWhitespace(asm):
    """
    Returns assembly array with comments and blank lines
    stripped away
    """

    # remove comments
    for i in range(len(asm)):
        for j in range(len(asm[i])):
            if asm[i][j] == "/" or asm[i][j] == "\n":
                asm[i] = asm[i][:j].replace(" ", "")
                break

    # remove blank lines 
    asm[:] = [i for i in asm if not i.isspace() and i]
    
    return asm

main()