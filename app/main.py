from typing import Annotated
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from contact_model import Contact

app = FastAPI()

app.mount("/static", StaticFiles(directory="static/"), "static")

templates = Jinja2Templates("templates/")

@app.get("/", response_class=HTMLResponse)
async def index():
    resp = RedirectResponse("/contacts")
    return resp


@app.get("/contacts", response_class=HTMLResponse)
async def contacts(req: Request):
    search = req.query_params.get("q")
    if search is not None:
        contact_set = Contact.search(search)
    else:
        contact_set = Contact.all()

    return templates.TemplateResponse(req, "index.html", context={"contacts": contact_set})


# HTMX Search
@app.post("/contacts", response_class=HTMLResponse)
async def search_contacts(req: Request, q: Annotated[str, Form()]):

    search = q
    if search is not None:
        contact_set = Contact.search(search)
    else:
        contact_set = Contact.all()

    return templates.TemplateResponse(req, "components/rows.html", context={"contacts": contact_set})


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
async def del_contact(c_id: int):
    c = Contact.find(c_id)
    c.delete()
    return RedirectResponse("/contacts", 303)
