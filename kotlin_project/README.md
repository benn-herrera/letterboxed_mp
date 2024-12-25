Solver for NYT Word Puzzle Letter Boxed
=======================================
* [Game Link](https://www.nytimes.com/puzzles/letter-boxed)
* [Tutorial](https://wordfinder.yourdictionary.com/blog/nyts-letter-boxed-a-quick-guide-to-the-fan-favorite-puzzle/)
* [Letterboxed Answers](https://letterboxedanswers.com) is a good source for test puzzles
* Regardless of the number of target words specified in the instructions for a given day there is always a two word solution.


TL;DR
------
* The puzzle is a box made of 12 unique letters, 3 to a side
* Use all the letters in as few words as possible****
* Each successive letter of a word must come from a different box side
* Each successive word must start with the last letter of the preceding word

Example
-------
```
 s  a  d
i       t
c       n
g       o
 r  u  h
```

* standing -> grouch would be one solution to this puzzle
  * There is always at least one two-word solution
  * There may be a one-word solution
* Examples of invalid words and solutions for this puzzle
  * cast: uses a and s in succession from the same side of the box
  * hogging: uses a doubled letter hits the same side twice in a row
  * grousing -> chat: first letter of second word is not the last letter of the first

Usage
-----
Enter the letters of the puzzle sides in the text field and hit "Solve"
![0_letterboxed_android_unsolved](https://github.com/user-attachments/assets/87835018-abd6-4e0a-b802-e06df594b60a)

Clear resets the puzzle to allow for entering another
![1_letterboxed_android solved](https://github.com/user-attachments/assets/acc8c622-51ac-4da1-bd33-eac522f31ade)

* First time of use downloads and caches a dictionary to local storage.
* Successive uses read the cached dictionary.

Sample Puzzles
--------------
* vrq wue isl dmo
* dng ruh iae ftm
* tdg nal kie ubh
* yde lis frn ovt
* rpj cit owl aks
* eid rah tyo bmn
