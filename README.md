# Smart Mirror - Eng Auth 2020

## A health focused smart mirror implementation in python

## Pose Estimation: Exercisor
Exercisor is an application widget developed for the smart-mirror operating system.
Exercisor is an exercise helper for the user.

### Features

- Save an iteration of a video with an exercise to use it as reference.
- Playback the reference exercises in a game-like environment.
  1. A human model playbacks the exercise.
  2. A pose estimation algorithm estimates the user's pose.
  3. The app compares the user's pose to the reference exercise.
  4. Corrective feedback arrows from the user's skeleton towards the correct pose
  are rendered to provide feedback regarding the user's performance.
  5. After each iteration of the exercise a score is calculated, depending on 
  the correctness of the execution.