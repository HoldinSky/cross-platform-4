# Mini-VM

### A simulation of a processor for laboratory work #4 of a "Cross-platform development" course

___

## Semantics

Data might be represented in 3 different ways:

* Integer
* Register reference
* Memory address

Syntax of each of mentioned above is presented in the following table.

| Type           | Syntax                                                                                                           | Example                     |
|----------------|------------------------------------------------------------------------------------------------------------------|-----------------------------|
| Number         | Integer in decimal form.                                                                                         | 10<br/>5<br/>-42<br/>0      |
| Register       | Starts with **%r**                                                                                               | %res<br/>%rxx               |
| Memory address | Enclosed in curly brackets **{}**. At least 1 character long. Consists of ASCII letters, digits and underscores. | {var_a}<br/>{age}<br/>{num} |

Machine has its own stack, organized in LIFO principle. Data in it might be manipulated via specific commands.
___

## Registers

| Name | Purpose                                                 |
|------|---------------------------------------------------------|
| %res | **IMMUTABLE**<br/>Stores results of commands execution. |
| %rxx | General use register. At start stores 0.                |

___

## Commands

| Action | Arguments                                                                          | Description                                                                                                                                                                |
|--------|------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| IDLE   | -                                                                                  | Machine doesn't perform any action                                                                                                                                         |
| PUSH   | 1 argument of any type:<br/>- integer<br/>- register<br/>- memory address          | Adds value represented by argument to the stack.<br/>**Halts if memory by the address is not allocated.**                                                                  |
| POP    | 1 argument of type:<br/>- memory address (optional)                                | Takes one value off of stack. Stores into memory if address is specified.<br/>**Halts if stack is empty.**                                                                 |
| INC    | 1 argument of any type:<br/>- integer<br/>- memory address<br/> - mutable register | Increments by one the value stored by the specified location. If the argument is integer, stores result in *%res*<br/>**Halts if memory by the address is not allocated.** |
| ADD    | 2 arguments of any type:<br/>- integer<br/>- register<br/>- memory address         | Adds 2 values and stores sum *%res* register.<br/>**Halts if memory by the address is not allocated.**                                                                     |
| SUB    | 2 arguments of any type:<br/>- integer<br/>- register<br/>- memory address         | Subtracts second value from first and stores result *%res* register.<br/>**Halts if memory by the address is not allocated.**                                              |
| STORE  | 2 arguments of any type:<br/>- integer (optional)<br/>- memory address             | Allocates memory by the specified address and stores the value in it or overwrites existing data. Takes value from *%res* register if first argument is not specified.     |
| LOAD   | 1 argument of type:<br/>- memory address                                           | Takes value by the specified address and stores it in *%rxx* register.<br/>**Halts if memory by the address is not allocated.**                                            |
| FREE   | 1 argument of type:<br/>- memory address                                           | Marks the memory by the address as unallocated.<br/>**Halts if memory by the address is not allocated.**                                                                   |
| PRINT  | 1 argument of any type:<br/>- integer<br/>- register<br/>- memory address          | Prints to specified output a value given or stored by the reference.<br/>**Halts if memory by the address is not allocated.**                                              |
