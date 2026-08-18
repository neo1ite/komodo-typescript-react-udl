interface User {
    id: number;
    name: string;
}

class Repository<T extends User> {
    private values: T[] = [];

    add(value: T): void {
        this.values.push(value);
    }

    find(id: number): T | undefined {
        for (const value of this.values) {
            if (value.id === id) {
                return value;
            }
        }
        return undefined;
    }
}

const repo = new Repository<User>();
repo.add({ id: 1, name: "Alice" });

// Uncomment to verify Komodo's TypeScript diagnostic underline:
// const wrong: number = "not a number";
