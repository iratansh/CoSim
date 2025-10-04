# ----------------------------------------------------------------
#
# CMPUT 229 Student Submission License
# Version 1.0
# Copyright 2022 Ishaan Ratanshi
#
# Unauthorized redistribution is forbidden in all circumstances. Use of this
# software without explicit authorization from the author or CMPUT 229
# Teaching Staff is prohibited.
#
# This software was produced as a solution for an assignment in the course
# CMPUT 229 - Computer Organization and Architecture I at the University of
# Alberta, Canada. This solution is confidential and remains confidential 
# after it is submitted for grading.
#
# Copying any part of this solution without including this copyright notice
# is illegal.
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
# --------------------------------------------------------------
# Name: Ishaan Ratanshi                 
# Lecture Section: LEC A1      
# Instructor: Rob Hackman          
# Lab Section: LAB D05        
# Teaching Assistant:   
# ---------------------------------------------------------------

.data
.align 2
	vector: 					#vector is an array of digits "455953"
		.word 4
		.word 5
		.word 5
		.word 9
		.word 5
		.word 3

.text
.include "common.s"

# -----------------------------------------------------------------------------
# creditValid: Validates and classifies a credit card number using Lunh's algorithm
#
# Args:
# 	a0: It has a pointer to the array of digits (32-bit integers) of a credit card number
# 	a1: Length of the array
#	a2: It is the space reserved for you to store the modified array of digits
# DESCRIPTION:
#
# Register Usage:
# t0 - base pointer for destination array (copy of a2)
# t1 - loop counter for forward/backward traversals
# t2 - current digit value being processed
# t3 - backward cursor within the destination array
# t4 - scratch register (constants or temporary pointers)
# t5 - running checksum of the processed digits
# t6 - parity flag (0 = skip double, 1 = double)
# a3 - preserved base pointer to the original digit array
# a4 - scratch register for offsets/comparisons in classification
# a5 - scratch register for checksum remainder/comparison loops
# -----------------------------------------------------------------------------

creditValid:

# ----------------------------------
#        STUDENT SOLUTION
# ----------------------------------
# Apply Lunh's algorithm step 1 - 4
# 1) Walk to the rightmost digit by advancing the pointer from a0 by 4 bytes each step (one word per element). Copy each digit into a2 as we go, but keep an untouched base pointer to a2 in a saved register while using a temporary cursor for the copy.
# 2) With the cursor now at the last digit in the copy, iterate backwards toward the base pointer. Track a parity flag in a register so the loop doubles every second digit starting from the second digit from the right.
# 3) When a doubled value exceeds 9, subtract 9 instead of splitting digits to keep the loop branch-light. Store the updated digit back through the backward-moving cursor.
# 4) Maintain a running checksum register that accumulates the current digit (doubled or untouched) during the backward pass.
# 5) Once the cursor returns to the base pointer, test whether the checksum is divisible by 10 and place the 0/1 validity result in the designated return register so the caller can consume it.
# 6) Then I got to do the classification of the card 
    mv t0, a2                  # Preserve base pointer of destination array
    mv t1, a1                  # t1 = number of digits remaining to copy
    mv a3, a0                  # Keep pointer to original digits for classification

COPY_LOOP:
    beqz t1, COPY_DONE
    lw t2, 0(a0)               # Load current digit from source array
    sw t2, 0(a2)               # Store digit into destination array
    addi a0, a0, 4             # Advance source pointer
    addi a2, a2, 4             # Advance destination pointer
    addi t1, t1, -1            # One fewer digit left to copy
    j COPY_LOOP

COPY_DONE:
    mv a2, t0                  # Restore destination pointer to its base
    mv t5, zero                # Set checksum
    mv t6, zero                # Parity flag starts at "skip doubling"
    beqz a1, RETURN_INVALID    # Zero-length input treated as invalid

    addi a4, a1, -1            # Compute offset to last element: (length-1) * 4
    slli a4, a4, 2
    add t3, t0, a4             # t3 = address of last digit in destination array
    mv t1, a1                  # Reset counter for backward traversal
    li t4, 9                   # Threshold for subtracting 9 after doubling

BACK_LOOP:
    lw t2, 0(t3)               # Fetch current digit from the end toward the front
    beqz t6, SKIP_DOUBLE       # If parity flag is 0, skip doubling
    slli t2, t2, 1             # Double the digit
    ble t2, t4, STORE_VALUE
    addi t2, t2, -9            # Adjust double-digit results by subtracting 9
    j STORE_VALUE

SKIP_DOUBLE:				   # Does what you expect it to do
    nop

STORE_VALUE:
    sw t2, 0(t3)               # Store possibly modified digit
    add t5, t5, t2             # Accumulate checksum
    xori t6, t6, 1             # Flip parity flag for next iteration
    addi t1, t1, -1            # One fewer digit left to process
    beqz t1, FINAL_CHECK
    addi t3, t3, -4            # Move cursor to previous digit
    j BACK_LOOP

FINAL_CHECK:
    li t4, 10                  # Prepare for modulo check
    mv a5, t5                  # Work on a copy of the checksum

MOD_LOOP:
    blt a5, t4, MOD_DONE
    addi a5, a5, -10
    j MOD_LOOP

MOD_DONE:
    bnez a5, RETURN_INVALID    # Non-zero remainder => invalid
    j CLASSIFY_CARD            # Valid number; determine card type

RETURN_INVALID:
    li a0, 0                   # Zero-length input or invalid checksum
    ret

CLASSIFY_CARD:
    li a0, 4                   # Default classification is unknown
    lw t2, 0(a3)               # First digit (MII)
    li t4, 4
    beq t2, t4, CHECK_VISA
    li t4, 5
    beq t2, t4, CHECK_MC
    li t4, 3
    beq t2, t4, CHECK_DC
RETURN_TYPE:
    ret

CHECK_VISA:
    li t4, 13
    beq a1, t4, VISA_RETURN    # 13-digit VISA (not Chase)
    li t4, 16
    bne a1, t4, RETURN_TYPE    # Only 13 or 16 digit cards are VISA

    la t4, vector              # Compare first six digits with Chase prefix
    mv a4, a3                  # a4 iterates over card digits
    li t1, 6

VISA_CHASE_LOOP:
    beqz t1, VISA_CHASE        # All six digits matched
    lw t2, 0(a4)
    lw t3, 0(t4)
    bne t2, t3, VISA_NONCHASE
    addi a4, a4, 4
    addi t4, t4, 4
    addi t1, t1, -1
    j VISA_CHASE_LOOP

VISA_CHASE:
    li a0, 12                  # VISA issued by Chase
    j RETURN_TYPE

VISA_NONCHASE:
    li a0, 1                   # VISA but not Chase
    j RETURN_TYPE

VISA_RETURN:
    li a0, 1                   # 13-digit VISA
    j RETURN_TYPE

CHECK_MC:
    li t4, 16
    bne a1, t4, RETURN_TYPE
    lw t2, 4(a3)               # Second digit
    li t3, 1
    beq t2, t3, MC_TYPE
    li t3, 2
    beq t2, t3, MC_TYPE
    li t3, 4
    beq t2, t3, MC_TYPE
    j RETURN_TYPE

MC_TYPE:
    li a0, 2
    j RETURN_TYPE

CHECK_DC:
    li t4, 14
    bne a1, t4, RETURN_TYPE
    lw t2, 4(a3)               # Second digit must be 0
    bnez t2, RETURN_TYPE
    lw t2, 8(a3)               # Third digit between 0 and 5 inclusive
    li t3, 5
    blt t3, t2, RETURN_TYPE
    li a0, 3
    j RETURN_TYPE
