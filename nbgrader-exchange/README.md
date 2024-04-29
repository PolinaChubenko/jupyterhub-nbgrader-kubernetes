# Nbgrader K8s Exchange

This is a modified version of the [default nbgrader exchange](https://nbgrader.readthedocs.io/en/stable/user_guide/what_is_nbgrader.html#filesystem-exchange) which works in a JupyterHub + Kubernetes environment.

## Key idea

The default exchange relies on the assumption, that the users are uniquely identifiable by their UNIX user ids (UIDs).
However, this assumption does not hold when running nbgrader on Kubernetes, where each student has their own pod with the same user (jovyan, UID=1000).
To address this issue, we reorganized the directory structure of the exchange to easily mount only the files of the respective student into their pod.
Therefore, the students have no access to the files of other students. The shared files that need to be accessible by all students simultaneously, should be mounted as "read-only" volumes.

## Directory structure

The directory structure of the default exchange is the following:

```
exchange
├── course101
│   ├── feedback
│   │   ├── 662a2398141ddb53.html
│   │   └── be4a67ab2876f854.html
│   ├── inbound
│   │   ├── studend1+assignment1+timestamp+random_string.ipynb
│   │   └── studend2+assignment1+timestamp+random_string.ipynb
│   └── outbound
│       ├── assignment1
│       │   └── assignment1.ipynb
│       └── assignment2
│           └── assignment2.ipynb
└── course102
    ├── feedback
    ├── inbound
    └── outbound
```

Directory structure of the modified exchange:

```
exchange
├── course101
│   ├── feedback
│   ├── feedback_public
│   │   ├── student1
│   │   │   └── 662a2398141ddb53.html
│   │   └── student2
│   │       └── be4a67ab2876f854.html
│   ├── inbound
│   │   ├── student1
│   │   │   └── assignment1+timestamp+random_string.ipynb
│   │   └── student2
│   │       └── assignment1+timestamp+random_string.ipynb
│   └── outbound
│       ├── assignment1
│       │   └── assignment1.ipynb
│       └── assignment2
│           └── assignment2.ipynb
└── course102
    ├── feedback
    ├── feedback_public
    ├── inbound
    └── outbound
```

The advantage of this structure is, that the directories can be mounted into the pods by the names of the students.
