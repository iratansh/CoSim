#
#CMPUT 229 Assignment Solution License
# Version 1.0
#
# Copyright 2017 University of Alberta --- all rights are reserved
# Copyright 2022 Vedant Vyas
# Unauthorized redistribution is forbidden in all circumstances. Use of this
# software without explicit authorization from the author or CMPUT 229
# Teaching Staff is prohibited.
#
# This software was produced as a solution for an assignment in the course
# CMPUT 229 - Computer Organization and Architecture I at the University of
# Alberta, Canada. This solution was produced by the teaching staff or their
# designates. This software is confidential and always remains confidential.
#
# Accessing, distributing, sharing of this software is illegal.
# Copying any portion of this software into another software
# without including this copyright notice is illegal.
#
# If any portion of this software is included in a solution submitted for
# grading at an educational institution, the submitter will be subject to
# the sanctions for plagiarism at that institution.
#
# If this software is found in any public website or public repository, the
# person finding it is kindly requested to immediately report, including
# the URL or other repository locating information, to the following email
# address:
#
#          cmput229@ualberta.ca
#
#-------------------------------
#
# Author: Vedant Vyas 
# Date: May 20, 2022
#
# Running this file in combination with the creditValid function
# results in TWO lines of output!
# This program reads a file and places it in memory. Then calls creditValid.s and prints the type of card and modified array depending on the return value from creditValid.s
#-------------------------------
#

.data
inputStream:    #space for input number to be stored
.space 2048
newline: .asciz "\n"
masterS: .asciz "MasterCard\n"
visaS:   .asciz "VISA\n"
dinerS: .asciz "Diner'sClub\n"
chaseS: .asciz "Chase\n"
unknownS: .asciz "Unknown\n"
invalidS: .asciz "Invalid\n"
creditCardNoS: .asciz "CreditCardNumber: "
noFileStr:
.asciz "Couldn't open specified file.\n"

.align 2
digArray:
.space 64       #space for digArray
result:         #beginning of the result word
.space 64
test:
.word 0

length:
.word 0


.text
#------------------------------------------------------------------------------
# main
# This function copies the number from input file and then saves it in inputStream. 
# And then calls function creditValid: and prints the type of card and modified array.
# 
# Register Usage:
#   t0: used to read unsigned bit from inputStream in 'copy:', pointer to result in 'printModifiedArray:'
#   t2: loads the value of length in 'printModifiedArray:'
#   t3: used as a counter in 'copy:'
#   t5: used to hold integers for comparison and temporary calculations
#   a0: used to hold filename pointer and as arguments for 'creditValid:' and system calls
#   a1: pointer to digArray in 'copy:'
#   a2: pointer to inputStream in 'copy:'
#-----------------------------------------------------------------------------
main:
    lw	    a0, 0(a1)	#Put the filename pointer into a0
    li	    a1, 0		#Flag: Read Only
    li	    a7, 1024	#Service: Open File
    #File descriptor gets saved in a0 unless an error happens
    ecall
    bltz	a0, main_err #Negative means open failed

    la	    a1, inputStream	#write into my binary space
    li	    a2, 2048        #read a file of at max 2kb
    li	    a7, 63          #Read File Syscall
    ecall
   

    la	    a2, inputStream	    #supply pointers as arguments
    la      a1, digArray        #a1 is the pointer to digArray
    li t3, 0

   #Reading the file
copy:
    addi t3, t3, 1              #adding 1 to t3 and storing it back to t3
    lbu t0, 0(a2)               #load an unsigned bit from contents of a2 with an offset of 0 
    li t5, 32
    beq t0, t5, copyDone        #stop storing characters once you encounter space
    li t5, 10
    beq t0, t5, copyDone        #stop storing characters once you encounter newline
    addi t0, t0, -48            #adding -48 to t0 and storing it back to t0 to convert ascii digits to numbers
    sw t0, 0(a1)                #storing the digit to address stored in a1 with an offset of 0
    addi a2, a2, 1              #adding 1 and storing it back to a2
    addi a1, a1, 4              #adding 4 and storing it back to a1
    bge t3, a0, copyDoneWithOutWS        #if t3 >= a0 then we are done copying, otherwise jump back to copy
    j copy
 
copyDoneWithOutWS: 
    addi t3, t3, 1              #incrementing the counter if there was no space and newline in the test file
copyDone:      
  
    addi t3, t3, -1
    mv a0, t3
  
    mv 	a1, t3
    #storing the length of the credit card number
    la t0, length
    sw a1, 0(t0)
    
    
    la      a0, digArray
    la 	    a2, result
    jal       creditValid      #call the student subroutine/jump to code under the label 'creditValid'
    
    beq a0, zero, invalidP	   #if a0 is zero, then its invalid
    li t0, 1
    beq a0, t0, visaP          #if a0 is 1, then its visa
    li t0, 12
    beq a0, t0, chaseP         #if a0 is 12 then its chase Visa
    li t0, 3
    beq a0, t0, dinerP         #if a0 is 3, then its diner
    li t0, 4
    beq a0, t0, unknownP       #if a0 is 4, then its unknown
    
    
    masterP:
    #printing "master"
    	la a0, masterS				
    	j printDone
    visaP:
    #printing "VISA"
    	la a0, visaS
    	j printDone
    chaseP:
    #printing "Chase"
    	la a0, chaseS
    	j printDone
    unknownP:
    	la a0, unknownS
    	j printDone
    dinerP:
    	la a0, dinerS
    	j printDone
    invalidP:
    	la a0, invalidS
    	j printDone
    
  printDone:
  	li a7, 4            #storing 4 in a7 which is syscall code to print string         
   	ecall               #make the actual call
   
 #printing the array after doubling and addition which was saved in the memory reserved by function creditValid  
 printModifiedArray:
   la t0, result            #copying the memory address of t0 to result
   lw t2, length            #loading the contents of length to t2
   slli t2, t2, 2           #left shifting t2 by 2 and then saving it to t2
   add t2, t2, t0           #adding t2 and t0 and then saving it back to t2
 modifiedArrayLoop:
  	
  	
  	lw a0, 0(t0)            #loading the content saved at the memory address stored in t0 with an offset of 0
  	addi t0, t0, 4          #adding t0 by 4 and saving it back to t0
  	li a7, 1                #storing 1 in a7 which is syscall code to print integer
  	ecall                   #make the actual call
  	beq t2, t0, modArrayLoopDone    #if content of t2 equals content of t0 jump to modArrayLoopDone, which means that we have printed the modified number
  	j modifiedArrayLoop         #if not then jump back to modifiedArrayLoop which means we still need to print
  
  modArrayLoopDone:
    j	    main_done

main_err:
    la	    a0, noFileStr   #print error message in the event of an error when trying to read a file
    li	    a7, 4
    ecall

main_done:
    li      a7, 10      #exit program syscall
    ecall

#-------------------end of common file-------------------------------------------------
