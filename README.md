DplTools
========

Data pipelining tools. Python library for manipulating heterogeneous scientific datasets as sequential data frames. 
Also known as "Data Pot Luck," allowing disparate instrument data streams to be brought to the same table for sharing.

This project is intended to provide simple, pragmatic tools for building science web apps, visualizations, filtering
and querying by focusing on atmospheric science instruments as "frame-streams". A frame-stream is a sequence of 
key-value groups which represent a timespan, zero or more data channels (as values including multidimensional arrays),
and eventually a projection onto the earth or atmosphere. 

As a stream, the datasets can represent stored data time ranges, or "real-time" content as it arrives. 

Filters for remapping, resampling, interpolating, and merging streams are part of the functional baseline. 

Applying this convention and tools has served as a useful simplifying model for a variety of ground-based and 
aircraft atmospheric instrumentation at UW-SSEC. Further work is needed, however, in order for the tools to be more 
widely adopted. 

Such future work includes generalized web service tools, core metadata management tools including query-by-example, 
and potential compatibility bridges with other data-flow based systems like VTK and LabView.

