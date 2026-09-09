import type { ReactNode } from "react";

export function Notice({kind="info",children}:{kind?:"info"|"success"|"warning"|"error";children:ReactNode}) {
  return <div className={`notice ${kind}`} role={kind==="error"?"alert":"status"}>{children}</div>;
}
export function Busy({label="Loading…"}:{label?:string}) { return <div className="inline-busy"><span className="loader" />{label}</div>; }
export function Empty({children}:{children:ReactNode}) { return <div className="empty-state compact-empty">{children}</div>; }
export function Status({value}:{value:string}) { return <span className={`record-status status-${value}`}>{value.replaceAll("_"," ")}</span>; }
export const readableDate = (value:string|null|undefined) => value ? new Date(value).toLocaleDateString(undefined,{day:"numeric",month:"short",year:"numeric"}) : "No date";
export const money = (value:string|number,currency="INR") => new Intl.NumberFormat(undefined,{style:"currency",currency,maximumFractionDigits:2}).format(Number(value));
export const minutes = (value:number) => value < 60 ? `${value} min` : `${Math.floor(value/60)}h ${value%60}m`;
export function FieldError({message}:{message:string}) { return message ? <Notice kind="error">{message}</Notice> : null; }
