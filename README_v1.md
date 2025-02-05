
# CHECK24 GenDev Streaming Package Comparison Challenge

This is a solution for the challenge of the 6th round of the GenDev Scholarship


## TL;DR

The CHECK24 GenDev Streaming Package Comparison Challenge was about creating an app to help users find the best streaming packages for watching their favorite teams' games. Here’s what I did:

The Goal: Users select their favorite teams, and the app compares packages to find the best one—or the best combination of up to four packages—covering the most matches for the lowest price.

Tech Stack:
I used Supabase for the database. The frontend was built in Swift, which I learned specifically for this project. The backend runs on Python with FastAPI, a framework I love for its speed and simplicity. For caching, I used Redis.

Filtering Games:
I focused on games at least 3 months ahead. To make it realistic, I included logic for detecting breaks in the schedule (e.g., winter or national breaks). If any games lacked streaming data, they were flagged to keep things transparent for users.

Prioritizing Games:
Not all games are equally important, so I gave extra weight to high-stakes matches, like title races, relegation battles, or finals. I also limited the solution to 4 packages to keep things practical.

The Algorithm:
I went with a Greedy Algorithm because it’s fast and works well for the scope of this project. For optimization, I chose Simulated Annealing since it balances simplicity and effectiveness.

Challenges & Lessons:
Balancing speed, accuracy, and user-friendliness was tough, especially with so much data. I also had to make trade-offs, like skipping some advanced features to meet the deadline. But the project gave me a chance to try new tools and problem-solving approaches, which was exciting.

Future Ideas:
Fine-tune game prioritization, improve top-game detection, experiment with hybrid algorithms, polish the frontend, and add better error handling.
This project was challenging but fun—especially learning Swift and working with new technologies under time pressure!
## What was the goal?

Build an application that allows users to compare the best streaming packages for watching their favorite teams' matches. Users can select one or more teams and receive a comparison of streaming packages based on the availability of the selected teams' games. If one package doesn't stream every match, the next step is to compute the best combination of packages. The combination of packages should cover as many games as possible while finding the lowest total price. The focus should be on comparing the most packages / finding the best combination in the given time.
## Screen Recording

https://www.loom.com/share/980bc32fbf03407e8662a5a6768ff4a0?sid=59b8f4a2-adc4-480f-a7ec-e158bc3d5a8d

## Techstack

I used Supabase as a databse. I've heard a lot of good things about it, but never got around to using it. Thanks to the strong free tier and the simple user interface, I was able to set up everything I needed in no time at all.

I chose Swift for the front end. Like Supabase, I have never been able to use Swift in a larger project. Since Check24 is focusing on an app, I thought I'd give it a try. Even though I learned Swift specifically for this project, or at least the basics, and you can see this in my code, it was still fun to try out new technologies. 

I used Python with Fastapi for the backend. Simply because I love Python and with the help of Fastapi you can make fast progress.

For caching, I used the standard redis.
## Where should be the limit for how far we look into the future?

The first question I asked myself was which games are we looking at for the algorithm at all? \
Just all of them? \
The ones in the next 6 months? 

That would probably have been the easiest solution. Although we are working with stiff data, I still wanted to keep the project as realistic as possible. \
Since I don't really know anything about soccer, I did some research and found out that the broadcasting rights don't change in the middle of the season, which is kind of logical. So I decided to go for the third option and I wanted to consider all the games until the end of the season. 

But what if the season has just started or is about to end? Then the algorithm would only look at very few games. \
So I thought about looking at least 3 months into the future in order to have enough games. Why 3 months? I think in 3 months you have enough games for a good recommendation but don't look too far into the future. The customer wants to see the games now and not in a year's time. 

But now we are again faced with the problem that we make a direct cut if we look at least 3 months into the future. Therefore, we have implemented a break search which automatically recognizes unusual breaks. The algorithm searches for breaks 6 months in the future, so we have solved the problem. 

We consider all games until a longer break (national games, winter break etc. ) which is at least 3 months in the future but maximum 6 months in the future. 

Now we have solved this problem, but this creates a new problem. Which break are we looking at? After all, different leagues have different systems. While these are all more or less the same in Europe, they can be drastically different from the MLS.

Now you could do this break detection dynamically for each league but that would be quite inconvenient and unnecessarily computationally intensive. That's why I decided to define a main league. The only reason for this is to decide from which league we take the next break in at least 3 months. 

How do we determine the main league? 
I have kept this very simple as all top 5 leagues have roughly the same cycle, let's take one of the top 5 leagues if it is in the search query. If there are several European clubs, you can compare them in the UEFA ranking. If there are only exotic leagues, one is taken at random. This could be improved in the future by having someone with soccer knowledge further break down the leagues. 

Another problem is that of the 9k games in the dataset, about 1/3 have no data on who is actually streaming them. But this is the most important value for us. Therefore, these are filtered out for the package recommendation from the beginning and shown separately in a yellow box in the frontend to be transparent with the user.






## How do we weight games?

Well, now we've decided which games we're going to consider. But not all games are equally important. If the request is particularly large, then we don't want to have to buy dozens of different packages. That's why I've set the maximum number of packages at 4. This is where the weighting comes into play. If not all games can be covered with 4 packages, we want to see the top games before we see others. For example, the algorithm should prefer a Champions League game to a game from the 2nd Bundesliga. We weight the games by looking at which competition it is. These weights are hard-coded and can be expanded as desired. 

Furthermore, we try to identify top games. We do this by determining the teams position in the table and then looking at whether both teams are in the top 3 (title fight) or the bottom 3 (relegation fight). 

We also look at whether the knockout competition is a semi-final, final, etc. 

For performance reasons, even with caching and batching, it was not advantageous to leave the top game detection and phase detection in the algorithm. Since a lot of time went into it, I left the code there anyway. 

Another consideration was to weight games higher over time. The same game can potentially be less important at the beginning of the season than at the very end. But since I couldn't confirm this thesis, I left this out.
## Which algorithm?

The options were Greedy + Optimization or Dynamic Programming. After all, this is a set cover problem. 

Although Dynamic Programming guarantees an optimal solution, the advantages of Greedy outweigh the disadvantages. DP can take a long time for larger requests, which can have a massive negative impact on the user experience. Greedy offers a fast usable first solution. In addition, the Greedy solution can progressively improve in the background, which always delivers a very good solution or even a perfect solution. 

Now you could have used DP for small queries, as it is mathematically correct and Greedy only approximates, but this was not possible due to time constraints.
## How can we optimize the algorithm? (Hill Climbing vs Simulated Annealing vs Tabu Search)

#### Hill Climbing 
Hill Climbing is the simplest strategy, where the algorithm always chooses the best immediate improvement. It is fast, easy to implement, and straightforward to understand. However, it often gets stuck in local optima and rarely finds the global best solution. For our specific problem—complex team combinations—this approach might be too simplistic.

#### Simulated Annealing 
Inspired by cooling processes in metallurgy, Simulated Annealing offers the advantage of escaping local optima and achieving a good balance between exploration and exploitation. This makes it particularly suitable for problems like this one, where the solution space contains many local optima. However, it requires parameter tuning (e.g., cooling rate) and is somewhat more complex to implement, with runtime being harder to predict.

#### Tabu Search 
Tabu Search uses memory to avoid recently visited solutions, making it highly effective for combinatorial problems. It prevents cycles and allows systematic exploration of the search space. However, it is the most complex to implement, has significant memory requirements due to the Tabu list, and might be overengineered for this problem.

Simulated Annealing is the best choice. It strikes a good balance between implementation effort and solution quality. Its strengths align well with the nature of our task, which involves a large number of packages (40), weightings. Additionally, it can be easily parallelized if needed.
## Future Optimizations and Improvements

On one hand, as already mentioned, the games can be weighted more finely. Be it by further differentiating the various tournaments and leagues or distributing other bonuses. 

We can also introduce better testing and error handling. 

We could also think about how to better identify top games. My implementation was already good but since it drastically worsened the api time performance I took it out. The algorithm still gives good recommendations and we could consider removing this bonus completely. 

Another improvement would be to improve the front end as I am not a front end expert it is kept very minimal. 

Another point is a hybrid algorithm. I have already explained in detail why we decided to use greedy, but for smaller queries it can make sense to use DP. Due to time constraints, I did not make it to the implementation. 
