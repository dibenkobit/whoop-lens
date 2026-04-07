"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  sectionKey: string;
  children: ReactNode;
};

type State = {
  hasError: boolean;
};

export class SectionErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Surface to console so developers can find it; production logging is out of scope.
    console.error(`Section "${this.props.sectionKey}" crashed:`, error, info);
  }

  componentDidUpdate(prevProps: Props): void {
    // Reset when the user switches sections.
    if (prevProps.sectionKey !== this.props.sectionKey && this.state.hasError) {
      this.setState({ hasError: false });
    }
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div className="rounded-2xl border border-rec-red/30 bg-rec-red/10 p-6 text-sm text-text-2">
          <p className="font-semibold text-rec-red">
            Something went wrong rendering the {this.props.sectionKey} section.
          </p>
          <p className="mt-2">
            Try switching to another section in the sidebar. If this keeps
            happening, please open a GitHub issue.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}
