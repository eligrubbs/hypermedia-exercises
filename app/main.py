from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse, FileResponse

from contact_model import Contact, Archiver


@asynccontextmanager
async def lifespan(app: FastAPI):
    Contact.load_db()
    yield


app = FastAPI(lifespan=lifespan)


app.mount("/static", StaticFiles(directory="static/"), "static")

templates = Jinja2Templates("templates/")

@app.get("/", response_class=HTMLResponse)
async def index():
    resp = RedirectResponse("/contacts")
    return resp


@app.get("/contacts", response_class=HTMLResponse)
async def contacts(req: Request, q: str="", page:int=1):
    search = q
    if search is not None:
        contact_set = Contact.search(search)
    else:
        contact_set = Contact.all()
    contact_set = Contact.paginate_set(contact_set, page)

    return templates.TemplateResponse(req, "index.html", context={"contacts": contact_set, "page": page, "search_query":q, "archiver": Archiver()})


# HTMX Search
@app.post("/contacts", response_class=HTMLResponse)
async def search_contacts(req: Request, q: Annotated[str, Form()], page: Annotated[int, Form()]):
    search = q
    if search is not None:
        contact_set = Contact.search(search)
    else:
        contact_set = Contact.all()
    contact_set = Contact.paginate_set(contact_set, page)

    resp = templates.TemplateResponse(req, "components/rows.html", context={"contacts": contact_set, "page":page, "search_query":q})

    return resp


@app.get("/contacts/new", response_class=HTMLResponse)
async def make_contact_page(req: Request):
    return templates.TemplateResponse(req, "new.html", context={"contact": Contact()})

@app.post("/contacts/new", response_class=HTMLResponse)
async def make_contact_post(req: Request):
    form_data = await req.form()
    c = Contact(
        None, form_data.get('first_name'),
        form_data.get('last_name'),form_data.get('phone'),form_data.get('email'),
    )
    if c.save():
        return RedirectResponse("/contacts", status_code=302)
    else:
        return templates.TemplateResponse(req, "new.html", context={"contact": c})


@app.get("/contacts/count", response_class=PlainTextResponse)
async def contact_count():
    # Mock taking a long time
    import asyncio
    await asyncio.sleep(1)
    return f"( {Contact.all().__len__()} total Contacts )"


@app.post("/contacts/archive")
async def save_offline_contacts(req: Request):
    archiver = Archiver.get()
    archiver.run()
    return templates.TemplateResponse("components/archive_ui.html", context={"request": req, "archiver":archiver})

@app.get("/contacts/archive")
async def get_saving_progress(req: Request):
    archiver = Archiver.get()
    return templates.TemplateResponse("components/archive_ui.html", context={"request": req, "archiver":archiver})


@app.get("/contacts/archive/file")
async def get_archive_file(req: Request):

    return FileResponse("contacts.json")

# @app.get("/messages")
# async def messages_hypermedia(self):
    
#     return


@app.get("/contacts/{c_id}", response_class=HTMLResponse)
async def show_contact(req: Request, c_id: int):
    c = Contact.find(c_id)
    print(c)
    return templates.TemplateResponse(req, "show.html", context={"contact":c})


@app.get("/contacts/{c_id}/edit", response_class=HTMLResponse)
async def edit_contact_page(req: Request, c_id: int):
    c = Contact.find(c_id)
    return templates.TemplateResponse(req, "edit.html", context={"contact": c})


@app.post("/contacts/{c_id}/edit", response_class=HTMLResponse)
async def edit_contact(req: Request, c_id: int):
    c = Contact.find(c_id)
    form_data = await req.form()
    c.update(form_data['first_name'], form_data['last_name'], form_data['phone'], form_data['email'])
    if c.save():
        return RedirectResponse("/contacts", status_code=302)
    else:
        return templates.TemplateResponse(req, "edit.html", context={"contact": c})


@app.delete("/contacts/{c_id}", response_class=HTMLResponse)
async def del_contact(req: Request, c_id: int):
    trigger = req.headers.get("HX-Trigger", 'WRONG')
    if trigger not in ['deleteBtn', 'rowDeleteBtn']:
        raise HTTPException(422, "Error")
    c = Contact.find(c_id)
    c.delete()
    if trigger == 'deleteBtn':
        return RedirectResponse("/contacts", 303)
    return HTMLResponse("")


@app.delete("/contacts", response_class=RedirectResponse)
async def del_many_contacts(req: Request):
    vals = req._query_params.getlist('selected_contact_ids')
    for val in vals:
        c = Contact.find(int(val))
        c.delete()
    return RedirectResponse("/contacts", 303)


@app.get("/contacts/{c_id}/email", response_class=PlainTextResponse)
async def email_validation(c_id: int, email: str):
    c = Contact.find(c_id)
    c.email = email
    c.validate()
    return c.errors.get('email', '')
