import random

# --- 1. Problem Setup ---

# Data structure for subjects, teachers, and classes
subjects = ["Math", "Science"]
teachers = ["Mr. Smith"]
classes = ["1A", "1B"]
time_slots = [(day, slot) for day in ["Mon", "Tue", "Wed", "Thu", "Fri"] for slot in range(3)]

# A "gene" is a single teaching event
# It will be a tuple: (class, subject, teacher, day, time_slot_index)
# We can represent the day and time slot with an index from 0 to 14 (5 days * 3 slots)
# Chromosome representation: A list of genes
# Each gene is (class, subject, teacher, timeslot_index)
num_lessons_per_class_and_subject = 1
num_lessons = len(classes) * len(subjects) * num_lessons_per_class_and_subject
# In this simple example, we need 4 lessons total (2 classes * 2 subjects)

# --- 2. Genetic Algorithm Functions ---

def create_individual():
    """Create a random individual (chromosome)."""
    chromosome = []
    # All lessons that need to be scheduled
    lessons_to_schedule = []
    for cls in classes:
        for subj in subjects:
            for _ in range(num_lessons_per_class_and_subject):
                lessons_to_schedule.append({'class': cls, 'subject': subj, 'teacher': teachers[0]})

    random.shuffle(time_slots)  # Shuffle time slots for random assignment
    
    # Assign each lesson to a random time slot
    for i, lesson in enumerate(lessons_to_schedule):
        gene = (lesson['class'], lesson['subject'], lesson['teacher'], time_slots[i])
        chromosome.append(gene)
    return chromosome

def fitness(chromosome):
    """Evaluate the fitness of a chromosome."""
    score = 0
    
    # Check hard constraints: No teacher or class double-booked at the same time
    teacher_schedule = {}
    class_schedule = {}
    for gene in chromosome:
        cls, subj, teacher, timeslot = gene
        
        # Teacher conflict
        if timeslot in teacher_schedule and teacher_schedule[timeslot] != teacher:
            score -= 100  # Large penalty
        teacher_schedule[timeslot] = teacher
        
        # Class conflict
        if timeslot in class_schedule and class_schedule[timeslot] != cls:
            score -= 100  # Large penalty
        class_schedule[timeslot] = cls

    # Check soft constraint: Subjects spread out over the week
    class_subject_days = {cls: {subj: set() for subj in subjects} for cls in classes}
    for gene in chromosome:
        cls, subj, _, (day, _) = gene
        class_subject_days[cls][subj].add(day)

    for cls in classes:
        for subj in subjects:
            if len(class_subject_days[cls][subj]) > 1:
                score += 10 # Small bonus for spreading out subjects
    
    return score

def select_parents(population):
    """Select parents using tournament selection."""
    pool_size = 5
    parents = random.sample(population, pool_size)
    parents.sort(key=fitness, reverse=True)
    return parents[0], parents[1]

def crossover(parent1, parent2):
    """Create a child using uniform crossover."""
    child = []
    for gene1, gene2 in zip(parent1, parent2):
        if random.random() < 0.5:
            child.append(gene1)
        else:
            child.append(gene2)
    return child

def mutate(chromosome, mutation_rate):
    """Mutate a chromosome with a small probability."""
    for i in range(len(chromosome)):
        if random.random() < mutation_rate:
            gene = list(chromosome[i])
            # Mutate the time slot by swapping with another
            all_other_times = list(time_slots)
            all_other_times.remove(gene[3])
            gene[3] = random.choice(all_other_times)
            chromosome[i] = tuple(gene)
    return chromosome

# --- 3. Main Algorithm Loop ---

def run_genetic_algorithm(generations, population_size, mutation_rate):
    """Main function to run the genetic algorithm."""
    population = [create_individual() for _ in range(population_size)]
    
    best_chromosome = None
    best_fitness = -float('inf')
    
    for generation in range(generations):
        # Evaluate fitness for all individuals
        population.sort(key=fitness, reverse=True)
        
        # Update best solution found so far
        current_best_fitness = fitness(population[0])
        if current_best_fitness > best_fitness:
            best_fitness = current_best_fitness
            best_chromosome = population[0]
            
        print(f"Generation {generation+1}: Best Fitness = {best_fitness}")
        
        # Create next generation
        new_population = [best_chromosome]  # Elitism: keep the best individual
        
        while len(new_population) < population_size:
            parent1, parent2 = select_parents(population)
            child = crossover(parent1, parent2)
            child = mutate(child, mutation_rate)
            new_population.append(child)
            
        population = new_population
        
        # Termination condition (if a perfect solution is found)
        if best_fitness >= 0:
            print("Optimal solution found.")
            break
            
    return best_chromosome

# --- 4. Execution ---

if __name__ == "__main__":
    best_solution = run_genetic_algorithm(
        generations=100, 
        population_size=50, 
        mutation_rate=0.1
    )
    
    print("\n--- Final Timetable ---")
    for lesson in best_solution:
        cls, subj, teacher, (day, slot) = lesson
        print(f"Class: {cls}, Subject: {subj}, Teacher: {teacher}, Day: {day}, Time Slot: {slot+1}")

