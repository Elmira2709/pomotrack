from typing import Annotated

from fastapi import FastAPI, Query

app = FastAPI()


@app.get("/items/")
async def read_items(q: Annotated[str | None, Query(title="Query string", min_length=3)] = None):
    query_items = {"q": q}
    return query_items