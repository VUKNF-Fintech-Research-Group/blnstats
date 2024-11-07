from prefect import flow, task, serve, deploy
import time

@task
def task_a():
    # Simulate some processing
    data = "Data from Task A"
    print("Task A completed.")
    return data

@task
def task_b1(data):
    # Process data in Task B1
    result_b1 = f"{data} processed by Task B1"
    print(f"Task B1 completed with result: {result_b1}")
    return result_b1

@task
def task_b2(data):
    # Process data in Task B2
    result_b2 = f"{data} processed by Task B2"
    print(f"Task B2 completed with result: {result_b2}")
    return result_b2

@task
def task_c(result_b1, result_b2):
    # Combine or further process the results from B1 and B2
    combined_result = f"Task C received: [{result_b1}] and [{result_b2}]"
    print(combined_result)
    return combined_result





@flow
def my_complex_flow():
    data = task_a()
    
    # Fork the flow into Task B1 and Task B2
    b1_result = task_b1(data)
    b2_result = task_b2(data)
    
    # Task C depends on both Task B1 and Task B2 result
    final_result = task_c(b1_result, b2_result)
    
    return final_result






@flow
def slow_flow(sleep: int = 60):
    "Sleepy flow - sleeps the provided amount of time (in seconds)."
    time.sleep(sleep)


@flow
def fast_flow():
    "Fastest flow this side of the Mississippi."
    return



# from prefect.utilities.visualization import TaskVizTracker, build_task_dependencies
from graphviz import Digraph


if __name__ == "__main__":
    # # Visualization test 1:
    # graph = my_complex_flow.visualize()
    # graph.filename = "custom_filename"
    # graph.render(format="png", cleanup=True)


    # # Visualization test 2:
    # graph = my_complex_flow.visualize()

    # # Render the graph to PNG in memory
    # png_data = graph.pipe(format='png')

    # # Write the PNG data to a file with your custom filename
    # with open('custom_filename.png', 'wb') as f:
    #     f.write(png_data)






    # Test 1:
    slow_deployment = slow_flow.to_deployment(name="sleeper")
    fast_deployment = fast_flow.to_deployment(name="fast")
    complex_deployment = my_complex_flow.to_deployment(name="complex")

    # Serve the deployments
    serve(
        slow_deployment,
        fast_deployment,
        complex_deployment
    )


    # Test 2:
    # my_complex_flow.serve(name="my_complex_flow", cron="* * * * *", webserver=True)

    # # Keep the script running
    # try:
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("Shutting down...")

