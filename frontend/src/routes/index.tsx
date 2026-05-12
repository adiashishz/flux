import { createBrowserRouter, Navigate } from "react-router-dom"
import { AppLayout } from "@/components/layout/AppLayout"
import { BoardList } from "@/features/board/BoardList"
import { BoardView } from "@/features/board/BoardView"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/boards" replace /> },
      { path: "boards", element: <BoardList /> },
      { path: "boards/:id", element: <BoardView /> },
    ],
  },
])
