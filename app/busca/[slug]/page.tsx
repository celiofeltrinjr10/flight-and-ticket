import { Suspense } from "react";
import Buscando from "./Buscando";

export default function Page() {
  return (
    <Suspense>
      <Buscando />
    </Suspense>
  );
}
