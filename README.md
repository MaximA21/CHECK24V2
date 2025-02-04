# CHECK24 V2

## Infrastructure Decisions

### AWS EC2 vs Lambda Comparison

I chose EC2 (initially t2.micro, upgraded to t2.medium) over Lambda for several reasons:

- Performance Evolution:
   - Initial response times on t2.micro: ~12 seconds
   - After vertical scaling to t2.medium: ~500ms
   - This improvement validates EC2 as the right choice for compute-intensive tasks
   - Shows potential for further optimization with dedicated resources

- Cost Considerations:
   - Lambda charges per request and compute time
   - Even with sub-second response times, costs can be unpredictable with varying load
   - EC2 provides predictable pricing for consistent workloads
   - Cost-effective when considering all required components

- Architecture Requirements:
   - Need for persistent Redis caching
   - Stateful rate limiting implementation
   - Complex monitoring setup (Prometheus, Grafana, Tempo)
   - These would require additional services in a Lambda setup

- Development & Debugging:
   - Easier local development with EC2-like environment
   - More straightforward debugging with full system access
   - Direct log access and monitoring
   - Simpler deployment process

- Performance Considerations:
   - No cold start penalties
   - Consistent compute resources
   - Ability to scale vertically when needed (as proven by our t2.micro to t2.medium upgrade)

### Domain & SSL
Using No-IP as DNS provider because:
- Free DNS solution
- Automatic IP updates
- SSL via Let's Encrypt for secure communication

## Application Architecture

### Process Management
Implemented Supervisor for process management:
- Automatic restart on crashes
- Log management
- Startup management

### Reverse Proxy (Nginx)
Set up Nginx as reverse proxy to:
- Handle SSL termination
- Route traffic to different services (API, Grafana, Prometheus)

## Performance Monitoring



### Prometheus
   - Collects metrics from FastAPI
   - Tracks request rates, latencies, and errors
   - Monitors system resources

### Grafana
   - Visualizes performance metrics
   - Custom dashboards for:
     - API performance (requests/second, latencies)
     - Algorithm efficiency
     - Resource utilization
     - Error rates

<img width="2241" alt="Screenshot 2025-02-04 at 18 46 50" src="https://github.com/user-attachments/assets/bc2680d0-f5b6-4e0c-b314-2b250b3fe216" />


### Tempo
   - Distributed tracing
   - Request flow visualization
   - Performance bottleneck identification

### Rate Limiting
Implemented rate limiting to:
- Prevent system overload
- Ensure fair resource distribution
- Protect against potential abuse
- Different limits for different endpoints based on complexity

## Performance Testing & Results

### Load Testing
Used Hey for load testing because:
- Simulates concurrent users
- Measures response times and error rates
- Provides detailed statistics
- Runs from outside EC2 for realistic results

### Performance Optimization

Initial Setup (t2.micro):
- Average response time: ~12s for complex queries
- Stable but slow performance
- No error issues under normal load

<img width="601" alt="Screenshot 2025-02-02 at 07 24 58" src="https://github.com/user-attachments/assets/04059929-a3e6-426e-8b77-d7a90d86d06f" />

Vertical Scaling (t2.medium):

- Dramatic performance improvement
- Average response time reduced to ~500ms
- Memory-intensive operations (like algorithm calculations) benefit significantly

<img width="587" alt="Screenshot 2025-02-04 at 09 23 59" src="https://github.com/user-attachments/assets/ff513f96-2d05-4281-b9be-e9368ba173d8" />


The vertical scaling proved to be a crucial optimization, showing that the algorithm was primarily compute-bound rather than I/O-bound. The 24x performance improvement justifies the moderate increase in infrastructure cost.

## Future Considerations

### Short Term
- Implement caching for frequently requested combinations
- Add more detailed tracing spans for algorithm phases
- Optimize database queries based on monitoring data

### Long Term

#### Advanced Architecture Evolution
1. WebSocket Implementation:
   - Replace current request/response model with real-time communication
 
   - Benefits:
     - Progressive result updates
     - Immediate partial result delivery
     - Better UX for complex queries

2. Load Balancing & Scaling:
   - Implement AWS Application Load Balancer
   - Multiple FastAPI instances for horizontal scaling
   - Auto-scaling based on:
     - CPU utilization
     - Memory usage
     - Request queue length

### Future Data & AI Integration

#### Live Data Pipeline Vision
- Web Scraping Enhancement:
   - Current: Selenium-based scraper for kicker.de (proof of concept)
   - Future: Crawl4AI implementation to:
     - Remove unnecessary HTML/content
     - Reduce token usage for LLM processing
     - Create clean, structured data for analysis

- Cloud-Based LLM Processing:
   - DeepSeek-R3 model hosted on AWS Bedrock:
     - Move from local inference to cloud
     - Better scalability and reliability
     - Integrated with existing AWS infrastructure
     - Easier monitoring and error handling

- Data Pipeline:

  
  ![Untitled Diagram drawio-3](https://github.com/user-attachments/assets/df51e8cd-675a-45e3-b429-aa9a7d7641bf)



   - Raw data backup in S3 for analysis
   - Extend existing monitoring stack:
     - Prometheus for metrics collection
     - Grafana for visualization
     - Tempo for tracing pipeline steps


## iOS App Optimization
- Enhanced error handling 
- Bug fixes 

